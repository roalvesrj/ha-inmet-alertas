"""Coordenador de dados da integração INMET Alertas.

Responsável por buscar o RSS principal e os CAPs individuais, tratar rate
limiting com fila de retry, mesclar alertas persistentes, disparar eventos e
notificações. A lógica pura de merge/expiração vive em
`helpers/persistence.py` (testável sem o harness do Home Assistant).
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import random
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    EVENT_ALERTA_PERIGOSO,
    EVENT_NOVO_ALERTA,
    HTTP_TIMEOUT,
    HTTP_TIMEOUT_TEST,
    MAX_DESCRIPTION_LENGTH,
    REQUEST_HEADERS,
    SEVERIDADE_CAP_MAP,
    SEVERIDADE_CORES,
    URL_RSS,
)
from .helpers.geo_processor import GeoProcessor
from .helpers.persistence import mesclar_alertas
from .utils import (
    check_state_affected,
    filter_state_municipalities,
    format_datetime,
    is_alert_active,
)

_LOGGER = logging.getLogger(__name__)


async def async_verificar_feed(hass: HomeAssistant) -> bool:
    """Verifica se o feed principal do INMET está acessível (usado no config flow)."""
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            URL_RSS, headers=REQUEST_HEADERS, timeout=HTTP_TIMEOUT_TEST
        ) as response:
            return response.status == 200
    except (aiohttp.ClientError, TimeoutError):
        return False


class INMETDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordenador para atualização de dados do INMET."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        estado: str,
        update_interval: int,
        notificacoes_perigo: bool,
    ) -> None:
        """Inicializar coordenador."""
        self.estado = estado
        self.notificacoes_perigo = notificacoes_perigo
        self._alertas_persistentes: dict[str, dict[str, Any]] = {}
        self._pending_caps: list[dict[str, Any]] = []
        self._retry_count: dict[str, int] = {}
        self._diagnostico: dict[str, Any] = {
            "ultimo_http_status": None,
            "rate_limit_hits": 0,
            "pending_caps": 0,
            "ultimo_erro": None,
            "total_alertas_api": 0,
            "ciclo_atual": None,
            "ultimo_ciclo_rate_limited": False,
            "ultimo_ciclo_com_erro": False,
        }

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval),
            config_entry=config_entry,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Buscar dados do INMET."""
        self._diagnostico["ciclo_atual"] = dt_util.now().isoformat()
        self._diagnostico["ultimo_ciclo_rate_limited"] = False
        self._diagnostico["ultimo_ciclo_com_erro"] = False

        try:
            session = async_get_clientsession(self.hass)

            # 1. Buscar RSS principal (todos os alertas)
            async with session.get(
                URL_RSS, headers=REQUEST_HEADERS, timeout=HTTP_TIMEOUT
            ) as response:
                self._diagnostico["ultimo_http_status"] = response.status
                if response.status != 200:
                    raise UpdateFailed(
                        f"Erro ao acessar o feed RSS: {response.status}"
                    )

                data = await response.text()

            if not data.strip():
                raise UpdateFailed("Resposta vazia do feed RSS")

            # Verificar rate limiting (não é erro, é comportamento esperado)
            if "limite de requisições" in data.lower() or "rate limit" in data.lower():
                self._diagnostico["rate_limit_hits"] += 1
                self._diagnostico["ultimo_ciclo_rate_limited"] = True
                _LOGGER.info(
                    "⏳ INMET aplicou rate limiting no RSS principal. "
                    "Processando apenas CAPs pendentes..."
                )

                alerts: list[dict[str, Any]] = []
                new_alert_ids: set[str] = set()
                now = dt_util.now()

                if self._pending_caps:
                    _LOGGER.info(
                        "Processando %d CAPs pendentes durante rate limiting...",
                        len(self._pending_caps),
                    )
                    await self._process_pending_caps(
                        session, alerts, new_alert_ids, now
                    )

                # Durante rate limiting, manter alertas existentes via persistência
                alertas_finais = await self._merge_alertas_com_persistencia(alerts, now)
                self._diagnostico["pending_caps"] = len(self._pending_caps)

                return {
                    "alerts": alertas_finais,
                    "count": len(alertas_finais),
                    "estado": self.estado,
                    "last_update": now.isoformat(),
                    "rate_limited": True,
                    "diagnostico": self._diagnostico.copy(),
                }

            if not data.strip().startswith("<?xml") and not data.strip().startswith(
                "<rss"
            ):
                _LOGGER.error(
                    "Resposta não é XML válido. Content-Type: %s",
                    response.headers.get("content-type", "N/A"),
                )
                _LOGGER.error("Primeiros 200 chars: %s", data[:200])
                raise UpdateFailed("INMET retornou conteúdo inválido (não é XML)")

            try:
                root = ET.fromstring(data)
            except ET.ParseError as e:
                _LOGGER.exception(
                    "Erro ao analisar XML. Primeiros 200 chars da resposta: %s",
                    data[:200],
                )
                raise UpdateFailed(f"XML inválido recebido do INMET: {e}") from e

            # Buscar items do RSS (com diferentes caminhos)
            items: list[ET.Element] = []
            item_paths = [
                ".//item",
                ".//entry",
                "./channel/item",
                './/*[local-name()="item"]',
            ]

            for path in item_paths:
                found_items = root.findall(path)
                if found_items:
                    items = found_items
                    break

            _LOGGER.debug("Processando %d alertas do RSS principal", len(items))
            self._diagnostico["total_alertas_api"] = len(items)

            # 2. Processar cada alerta individualmente (máximo 50 por ciclo)
            alerts = []
            new_alert_ids = set()
            now = dt_util.now()
            processed_count = 0
            max_caps_per_cycle = 50

            # Primeiro processar CAPs pendentes de tentativas anteriores
            if self._pending_caps:
                _LOGGER.info(
                    "Processando %d CAPs pendentes...", len(self._pending_caps)
                )
                await self._process_pending_caps(session, alerts, new_alert_ids, now)

            # Depois processar novos itens (limitado)
            for item in items:
                if processed_count >= max_caps_per_cycle:
                    _LOGGER.info(
                        "Limite de %d CAPs por ciclo atingido. "
                        "Restantes serão processados na próxima atualização.",
                        max_caps_per_cycle,
                    )
                    break

                try:
                    alert_data = await self._process_alert_item(session, item, now)
                    if alert_data:
                        alerts.append(alert_data)
                        new_alert_ids.add(alert_data["id"])
                        processed_count += 1

                        # Verificar se é um novo alerta
                        if alert_data["id"] not in self._alertas_persistentes:
                            await self._handle_new_alert(alert_data)

                    # Delay com jitter para evitar padrões de requisição
                    await asyncio.sleep(0.5 + random.uniform(0.1, 0.3))

                except Exception:  # noqa: BLE001 — um alerta com erro não derruba o ciclo
                    _LOGGER.exception("Erro ao processar alerta")
                    continue

            # Capturar IDs anteriores para limpeza de notificações
            previous_ids = set(self._alertas_persistentes.keys())

            # Merge inteligente de alertas para preservar persistência
            alertas_finais = await self._merge_alertas_com_persistencia(alerts, now)

            # Limpar notificações de alertas realmente expirados
            await self._cleanup_expired_notifications(alertas_finais, previous_ids)

            _LOGGER.info(
                "Processamento concluído: %d alertas persistentes para %s",
                len(alertas_finais),
                self.estado,
            )
            _LOGGER.info("  - Novos do scan atual: %d", len(alerts))
            _LOGGER.info(
                "  - Mantidos de scans anteriores: %d",
                len(alertas_finais) - len(alerts),
            )
            _LOGGER.info(
                "CAPs pendentes para próxima tentativa: %d", len(self._pending_caps)
            )
            self._diagnostico["pending_caps"] = len(self._pending_caps)

            return {
                "alerts": alertas_finais,
                "count": len(alertas_finais),
                "estado": self.estado,
                "last_update": now.isoformat(),
                "diagnostico": self._diagnostico.copy(),
            }

        except Exception as e:  # noqa: BLE001 — normaliza erro para UpdateFailed
            # Rate limiting não é erro - já foi tratado acima
            error_msg = str(e).lower()
            if "rate limiting" in error_msg or "limite de requisições" in error_msg:
                _LOGGER.debug(
                    "Rate limiting detectado, mantendo alertas persistentes: %s", e
                )
                self._diagnostico["ultimo_ciclo_rate_limited"] = True

                # Mesmo durante erro de rate limiting, manter alertas válidos
                alertas_finais = await self._merge_alertas_com_persistencia(
                    [], dt_util.now()
                )
                self._diagnostico["pending_caps"] = len(self._pending_caps)

                return {
                    "alerts": alertas_finais,
                    "count": len(alertas_finais),
                    "estado": self.estado,
                    "last_update": dt_util.now().isoformat(),
                    "rate_limited": True,
                    "diagnostico": self._diagnostico.copy(),
                }

            self._diagnostico["ultimo_erro"] = str(e)[:200]
            self._diagnostico["ultimo_ciclo_com_erro"] = True
            raise UpdateFailed(f"Erro ao atualizar dados: {e}") from e

    async def _process_pending_caps(
        self, session, alerts: list, new_alert_ids: set, now: datetime
    ) -> None:
        """Processar CAPs que falharam em tentativas anteriores."""
        retry_caps = []

        for cap_info in self._pending_caps[:10]:  # Máximo 10 retries por ciclo
            try:
                # Delay extra para retries
                await asyncio.sleep(1.0 + random.uniform(0.2, 0.5))

                alert_data = await self._process_alert_item(
                    session, cap_info["item"], now, retry=True
                )
                if alert_data:
                    alerts.append(alert_data)
                    new_alert_ids.add(alert_data["id"])
                    _LOGGER.debug(
                        "✅ CAP %s processado com sucesso no retry", cap_info["id"]
                    )
                    # Resetar contagem ao obter sucesso
                    self._retry_count[cap_info["id"]] = 0
                else:
                    # Ainda com problemas - manter na fila com backoff por ciclos
                    self._retry_count[cap_info["id"]] = (
                        self._retry_count.get(cap_info["id"], 0) + 1
                    )
                    tentativa = self._retry_count[cap_info["id"]]

                    if tentativa <= 10:
                        retry_caps.append(cap_info)
                        _LOGGER.debug(
                            "🔄 CAP %s ainda com rate limiting, tentativa %d",
                            cap_info["id"],
                            tentativa,
                        )
                    else:
                        # Após 10 tentativas, resetar a contagem para continuar
                        # tentando, mas com prioridade menor (fim da fila)
                        _LOGGER.info(
                            "🔄 CAP %s ainda com rate limiting após %d tentativas, "
                            "resetando contagem",
                            cap_info["id"],
                            tentativa,
                        )
                        self._retry_count[cap_info["id"]] = 0
                        retry_caps.append(cap_info)

            except Exception as e:  # noqa: BLE001 — mantém o CAP na fila
                error_msg = str(e).lower()
                if "rate limiting" in error_msg or "limite de requisições" in error_msg:
                    _LOGGER.debug(
                        "Rate limiting persistente para CAP %s", cap_info["id"]
                    )
                else:
                    _LOGGER.warning(
                        "Erro no retry do CAP %s: %s", cap_info["id"], e
                    )

                # Manter na fila sem limite de tentativas
                self._retry_count[cap_info["id"]] = (
                    self._retry_count.get(cap_info["id"], 0) + 1
                )
                if self._retry_count[cap_info["id"]] <= 10:
                    retry_caps.append(cap_info)
                else:
                    self._retry_count[cap_info["id"]] = 0
                    retry_caps.append(cap_info)

        # Atualizar lista de pendentes (os que falharam voltam para a fila)
        self._pending_caps = retry_caps + self._pending_caps[10:]

    async def _merge_alertas_com_persistencia(
        self, novos_alertas: list, agora: datetime
    ) -> list:
        """Merge inteligente entre alertas existentes e novos.

        Preserva alertas que saíram do RSS mas ainda não expiraram e remove os
        expirados — a lógica pura está em `helpers/persistence.py`.
        """
        ids_antes = set(self._alertas_persistentes)
        ids_scan = {alerta["id"] for alerta in novos_alertas}

        try:
            alertas_finais, cache = mesclar_alertas(
                self._alertas_persistentes, novos_alertas, agora
            )
        except Exception:  # noqa: BLE001 — em erro, pelo menos os novos
            _LOGGER.exception("Erro no merge de alertas")
            return novos_alertas

        self._alertas_persistentes = cache
        ids_depois = set(cache)

        novos = len(ids_scan - ids_antes)
        mantidos = len(ids_antes & ids_depois)
        removidos = len(ids_antes - ids_depois)

        if mantidos > 0 or removidos > 0:
            _LOGGER.info("🔄 Merge de alertas concluído:")
            _LOGGER.info("  ✨ Novos: %d", novos)
            _LOGGER.info("  📌 Mantidos: %d", mantidos)
            _LOGGER.info("  ⏰ Removidos (expirados): %d", removidos)
            _LOGGER.info("  📊 Total final: %d", len(cache))

        return alertas_finais

    async def _cleanup_expired_notifications(
        self, current_alerts: list, previous_ids: set | None = None
    ) -> None:
        """Limpar notificações de alertas que não estão mais ativos."""
        if not previous_ids:
            return

        try:
            current_alert_ids = {alert["id"] for alert in current_alerts}
            expired_alert_ids = previous_ids - current_alert_ids

            for expired_id in expired_alert_ids:
                notification_id = f"inmet_alert_{self.estado}_{expired_id}"
                with contextlib.suppress(Exception):
                    await self.hass.services.async_call(
                        "persistent_notification",
                        "dismiss",
                        {"notification_id": notification_id},
                    )

        except Exception:  # noqa: BLE001
            _LOGGER.exception("Erro na limpeza de notificações")

    async def _process_alert_item(
        self, session, item, now: datetime, retry: bool = False
    ) -> dict[str, Any] | None:
        """Processar um item de alerta individual."""
        try:
            # Extrair dados básicos do item
            title_elem = item.find("title")
            link_elem = item.find("link")
            guid_elem = item.find("guid")
            pubdate_elem = item.find("pubDate")

            if not all(
                [title_elem is not None, link_elem is not None, guid_elem is not None]
            ):
                return None

            title = title_elem.text.strip() if title_elem.text else ""
            link = link_elem.text.strip() if link_elem.text else ""
            alert_id = guid_elem.text.strip() if guid_elem.text else ""
            pub_date = (
                pubdate_elem.text
                if pubdate_elem is not None and pubdate_elem.text
                else ""
            )

            if not retry:
                _LOGGER.debug("Processando alerta %s: %s", alert_id, title)

            # Verificar se o alerta afeta o estado configurado
            cap_data = await self._get_cap_data_with_retry(
                session, link, alert_id, item, retry
            )
            if not cap_data:
                return None

            if not check_state_affected(cap_data, self.estado):
                return None

            # Verificar se o alerta está ativo (dentro do período de validade)
            if not is_alert_active(cap_data, now):
                _LOGGER.debug("Alerta %s está fora do período de validade", alert_id)
                return None

            # Extrair nome do alerta (sem severidade)
            alerta_nome = re.sub(r"\. Severidade Grau:.*", "", title).strip()

            # Mapear severidade CAP para INMET
            severidade_cap = cap_data.get("severity", "")
            severidade_inmet = SEVERIDADE_CAP_MAP.get(
                severidade_cap, cap_data.get("severidade_titulo", "Desconhecida")
            )

            # Ícone baseado na severidade
            icone = SEVERIDADE_CORES.get(severidade_inmet or "Desconhecida", "ℹ️")

            # Formatar datas
            inicio_formatado = format_datetime(cap_data.get("onset", ""))
            fim_formatado = format_datetime(cap_data.get("expires", ""))

            # Filtrar municípios do estado
            municipios_estado = filter_state_municipalities(
                cap_data.get("municipios", ""), self.estado
            )

            return {
                "id": alert_id,
                "titulo": alerta_nome,
                "evento": cap_data.get("event", "Desconhecido"),
                "severidade": severidade_inmet,
                "severidade_cap": severidade_cap,
                "icone": icone,
                "inicio": inicio_formatado,
                "fim": fim_formatado,
                "onset": cap_data.get("onset", ""),  # ISO original p/ validação
                "expires": cap_data.get("expires", ""),  # ISO original p/ validação
                "descricao": cap_data.get("description", ""),
                "instrucoes": cap_data.get("instruction", ""),
                "municipios_estado": municipios_estado,
                "total_municipios_estado": len(municipios_estado),
                "link": link,
                "ativo": True,  # Todos retornados são ativos
                "publicado": pub_date,
                "area_desc": cap_data.get("area_desc", ""),
                "cor_oficial": cap_data.get("color_risk", ""),
                "url_grafica": cap_data.get("web", ""),
                "color_risk": cap_data.get("color_risk", ""),  # compatibilidade
                "dados_geograficos": cap_data.get(
                    "dados_geograficos"
                ),  # geometria processada
            }

        except Exception:  # noqa: BLE001
            _LOGGER.exception("Erro ao processar item do alerta")
            return None

    async def _get_cap_data_with_retry(
        self, session, url: str, alert_id: str, item, is_retry: bool = False
    ) -> dict[str, Any] | None:
        """Obter dados CAP com tratamento de rate limiting e retry automático."""
        try:
            cap_data = await self._get_cap_data(session, url)
            # Se conseguiu obter dados, garantir que não há pending duplicado
            if cap_data and not is_retry:
                self._remove_pending_cap(alert_id)
            return cap_data

        except Exception as e:  # noqa: BLE001
            error_msg = str(e).lower()

            # Detectar rate limiting ou problemas de conectividade
            if any(
                term in error_msg
                for term in [
                    "rate limiting",
                    "limite de requisições",
                    "connection reset",
                    "timeout",
                ]
            ):
                if not is_retry:
                    # Só adicionar à fila de pending se ainda não estiver
                    if not self._is_pending_cap(alert_id):
                        cap_info = {
                            "id": alert_id,
                            "url": url,
                            "item": item,  # Guardar o item completo para retry
                        }
                        self._pending_caps.append(cap_info)
                        _LOGGER.debug(
                            "⏳ CAP %s adicionado à fila de retry "
                            "(rate limiting temporário)",
                            alert_id,
                        )
                    else:
                        _LOGGER.debug(
                            "⏳ CAP %s já está na fila de retry, ignorando duplicata",
                            alert_id,
                        )
                    return None

                # Em retry, apenas debug - não é erro
                _LOGGER.debug(
                    "Retry ainda com rate limiting para CAP %s - tentará novamente",
                    alert_id,
                )
                return None

            # Erro diferente de rate limiting, logar e seguir
            _LOGGER.exception("Erro ao obter CAP %s", url)
            return None

    def _is_pending_cap(self, alert_id: str) -> bool:
        """Verificar se um alerta já está na fila de pending."""
        return any(cap["id"] == alert_id for cap in self._pending_caps)

    def _remove_pending_cap(self, alert_id: str) -> None:
        """Remover um alerta da fila de pending se presente."""
        self._pending_caps = [
            cap for cap in self._pending_caps if cap["id"] != alert_id
        ]
        # Resetar contagem de retry quando o CAP é removido com sucesso
        self._retry_count[alert_id] = 0

    async def _get_cap_data(self, session, url: str) -> dict[str, Any] | None:
        """Obter dados CAP (Common Alerting Protocol) do alerta específico."""
        try:
            async with session.get(
                url, headers=REQUEST_HEADERS, timeout=HTTP_TIMEOUT
            ) as response:
                if response.status != 200:
                    _LOGGER.warning(
                        "Erro ao acessar RSS específico: %s", response.status
                    )
                    return None

                data = await response.text()

            if not data.strip():
                _LOGGER.warning("Resposta vazia do CAP: %s", url)
                return None

            # Verificar rate limiting no CAP
            if "limite de requisições" in data.lower() or "rate limit" in data.lower():
                _LOGGER.info(
                    "⏳ Rate limiting detectado no CAP %s - será tentado novamente",
                    url,
                )
                raise Exception("Rate limiting")

            # Verificar se é XML válido antes de tentar processar
            if not data.strip().startswith("<?xml") and not data.strip().startswith(
                "<alert"
            ):
                _LOGGER.warning("CAP não é XML válido. URL: %s", url)
                _LOGGER.debug("Conteúdo recebido: %s", data[:100])
                return None

            root = ET.fromstring(data)

            # Namespace CAP
            ns = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}
            cap_data: dict[str, Any] = {}

            # Elementos diretos do alert
            for field in ["identifier", "sender", "sent", "status", "msgType"]:
                elem = root.find(f"cap:{field}", ns)
                if elem is not None and elem.text:
                    cap_data[field] = elem.text.strip()

            # Elementos do info
            info = root.find("cap:info", ns)
            if info is not None:
                for field in [
                    "language",
                    "category",
                    "event",
                    "severity",
                    "urgency",
                    "certainty",
                    "onset",
                    "expires",
                    "description",
                    "instruction",
                    "web",
                    "contact",
                ]:
                    elem = info.find(f"cap:{field}", ns)
                    if elem is not None and elem.text:
                        cap_data[field] = elem.text.strip()

                # Parâmetros
                for param in info.findall("cap:parameter", ns):
                    name_elem = param.find("cap:valueName", ns)
                    value_elem = param.find("cap:value", ns)

                    if (
                        name_elem is not None
                        and name_elem.text
                        and value_elem is not None
                        and value_elem.text
                    ):
                        param_name = name_elem.text.strip()
                        param_value = value_elem.text.strip()

                        if param_name == "ColorRisk":
                            cap_data["color_risk"] = param_value
                        elif param_name == "Municipios":
                            cap_data["municipios"] = param_value
                        elif param_name == "Estados":
                            cap_data["estados"] = param_value

                # Área e dados geográficos
                areas = info.findall("cap:area", ns)
                if not areas:
                    areas = info.findall(".//area")

                areas_desc = []
                poligonos = []

                for area in areas:
                    # Descrição da área
                    area_desc = area.find("cap:areaDesc", ns)
                    if area_desc is None:
                        area_desc = area.find("areaDesc")
                    if area_desc is not None and area_desc.text:
                        areas_desc.append(area_desc.text.strip())

                    # Polígonos - usar múltiplas estratégias
                    polygon_elem = area.find("cap:polygon", ns)
                    if polygon_elem is None:
                        polygon_elem = area.find("polygon")
                    if polygon_elem is None:
                        # Busca recursiva
                        for child in area.iter():
                            if child.tag.endswith("polygon"):
                                polygon_elem = child
                                break

                    if polygon_elem is not None and polygon_elem.text:
                        polygon_text = polygon_elem.text.strip()
                        if polygon_text:
                            poligonos.append(polygon_text)
                            _LOGGER.debug(
                                "Polígono extraído: %s...", polygon_text[:100]
                            )

                cap_data["area_desc"] = "; ".join(areas_desc)
                cap_data["polygons"] = poligonos

                # Processar dados geográficos se existirem polígonos
                if poligonos:
                    _LOGGER.info(
                        "Processando %d polígonos encontrados", len(poligonos)
                    )
                    try:
                        dados_geo = []
                        area_total = 0.0

                        for i, polygon_text in enumerate(poligonos):
                            resultado_geo = GeoProcessor.processar_poligono_completo(
                                polygon_text, f"alerta_{i}"
                            )
                            if resultado_geo:
                                dados_geo.append(resultado_geo)
                                area_total += resultado_geo.get("area_km2", 0)

                        # Combinar dados geográficos
                        if dados_geo:
                            dados_combinados = GeoProcessor.combinar_poligonos_estado(
                                dados_geo
                            )

                            cap_data["dados_geograficos"] = {
                                "poligonos_individuais": dados_geo,
                                "area_total_km2": dados_combinados["area_total_km2"],
                                "centro_geografico": dados_combinados["centro_estado"],
                                "bounding_box": dados_combinados["bounding_box_estado"],
                                "zoom_recomendado": dados_combinados["zoom_estado"],
                                "total_poligonos": len(dados_geo),
                            }

                            _LOGGER.info(
                                "Dados geográficos processados: %d polígonos, %s km²",
                                len(dados_geo),
                                dados_combinados["area_total_km2"],
                            )
                    except Exception:  # noqa: BLE001
                        _LOGGER.exception("Erro ao processar dados geográficos")
                        cap_data["dados_geograficos"] = None

            return cap_data

        except Exception as e:  # noqa: BLE001
            error_msg = str(e).lower()
            # Rate limiting não é erro - é comportamento normal da API
            if "rate limit" in error_msg or "limite de requisições" in error_msg:
                _LOGGER.debug("Rate limiting aplicado para %s - normal", url)
                return None

            _LOGGER.exception("Erro ao processar RSS específico %s", url)
            # Se for erro de conexão, tentar novamente
            if "Connection reset by peer" in str(e) or "timeout" in str(e).lower():
                raise Exception("Erro de conectividade - retry necessário") from e
            return None

    async def _handle_new_alert(self, alert_data: dict[str, Any]) -> None:
        """Lidar com novo alerta detectado."""
        _LOGGER.info("Novo alerta detectado: %s", alert_data["titulo"])

        # Disparar evento no Home Assistant
        self.hass.bus.async_fire(
            EVENT_NOVO_ALERTA,
            {
                "alert_id": alert_data["id"],
                "titulo": alert_data["titulo"],
                "severidade": alert_data["severidade"],
                "evento": alert_data["evento"],
                "estado": self.estado,
                "inicio": alert_data["inicio"],
                "fim": alert_data["fim"],
                "municipios": alert_data.get("total_municipios_estado", 0),
                "area_desc": alert_data.get("area_desc", ""),
                "descricao": alert_data.get("descricao", ""),
                "ativo": alert_data["ativo"],
            },
        )

        # Disparar evento específico para alertas perigosos
        if alert_data["severidade"] in ["Perigo", "Grande Perigo"]:
            self.hass.bus.async_fire(
                EVENT_ALERTA_PERIGOSO,
                {
                    "alert_id": alert_data["id"],
                    "titulo": alert_data["titulo"],
                    "severidade": alert_data["severidade"],
                    "evento": alert_data["evento"],
                    "estado": self.estado,
                    "inicio": alert_data["inicio"],
                    "fim": alert_data["fim"],
                    "municipios": alert_data.get("total_municipios_estado", 0),
                    "area_desc": alert_data.get("area_desc", ""),
                    "descricao": alert_data.get("descricao", ""),
                },
            )

        # Enviar notificação persistente se configurado
        if self.notificacoes_perigo and alert_data["severidade"] in [
            "Perigo",
            "Grande Perigo",
        ]:
            descricao = alert_data.get("descricao", "")
            if len(descricao) > MAX_DESCRIPTION_LENGTH:
                descricao = descricao[:MAX_DESCRIPTION_LENGTH] + "..."

            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": (
                        f"🚨 Alerta Meteorológico - {alert_data['severidade']} "
                        f"({self.estado})"
                    ),
                    "message": (
                        f"**{alert_data['titulo']}**\n\n"
                        f"Evento: {alert_data['evento']}\n"
                        f"Estado: {self.estado}\n"
                        f"Início: {alert_data['inicio']}\n"
                        f"Fim: {alert_data['fim']}\n"
                        f"Municípios afetados: "
                        f"{alert_data.get('total_municipios_estado', 0)}\n\n"
                        f"{descricao}"
                    ),
                    "notification_id": f"inmet_alert_{self.estado}_{alert_data['id']}",
                },
            )


# Tipo da config entry desta integração (runtime_data = coordenador)
type InmetAlertasConfigEntry = ConfigEntry[INMETDataUpdateCoordinator]
