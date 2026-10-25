"""Integração INMET Alertas para Home Assistant."""
from __future__ import annotations

import logging
from pathlib import Path

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    CARD_ALERTAS_JS,
    CONF_ESTADO,
    CONF_NOTIFICACOES_PERIGO,
    CONF_UPDATE_INTERVAL,
    DEFAULT_NOTIFICACOES_PERIGO,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    ESTADOS_BRASILEIROS,
    SERVICE_ATUALIZAR_ALERTAS,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_ATUALIZAR_ALERTAS_SCHEMA = vol.Schema(
    {vol.Optional(CONF_ESTADO): vol.In(sorted(ESTADOS_BRASILEIROS))}
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Configuração inicial: rota estática do plugin e serviço de atualização."""

    async def handle_atualizar_alertas(call: ServiceCall) -> None:
        """Força a atualização dos coordenadores carregados."""
        estado_param = call.data.get(CONF_ESTADO)
        coordenadores = []
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.state is not ConfigEntryState.LOADED:
                continue
            coordenador = entry.runtime_data
            if estado_param is None or coordenador.estado == estado_param:
                coordenadores.append(coordenador)

        if estado_param is not None and not coordenadores:
            raise ServiceValidationError(
                "Nenhuma configuração do INMET Alertas carregada para o estado "
                f"{estado_param}"
            )

        for coordenador in coordenadores:
            try:
                await coordenador.async_refresh()
            except Exception as err:  # noqa: BLE001 — falha de execução vira HA error
                raise HomeAssistantError(
                    f"Falha ao atualizar os alertas do INMET: {err}"
                ) from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_ATUALIZAR_ALERTAS,
        handle_atualizar_alertas,
        schema=SERVICE_ATUALIZAR_ALERTAS_SCHEMA,
    )

    await _async_registrar_recurso_estatico(hass)
    _agendar_registro_card(hass)

    return True


async def _async_registrar_recurso_estatico(hass: HomeAssistant) -> None:
    """Registra /<domain> → www/ para o plugin de mapa."""
    if hass.http is None:
        _LOGGER.debug("HTTP indisponível; plugin de mapa não será servido")
        return

    # Import tardio: mantém o pacote leve para os testes unitários (sem HA)
    from homeassistant.components.http import StaticPathConfig

    # Caminho relativo ao próprio módulo (robusto p/ qualquer diretório de config)
    plugin_path = Path(__file__).parent / "www"
    if not await hass.async_add_executor_job(plugin_path.is_dir):
        _LOGGER.warning("Pasta do plugin não encontrada: %s", plugin_path)
        return

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(f"/{DOMAIN}", str(plugin_path), False)]
        )
    except RuntimeError:
        # Rota já registrada (ex.: outro reload no mesmo processo)
        _LOGGER.debug("Recurso estático já registrado para %s", DOMAIN)
    else:
        _LOGGER.info(
            "✅ Plugin INMET disponível em: /%s/plugin_inmet_polygons.js",
            DOMAIN,
        )


@callback
def _registrar_card_no_frontend(hass: HomeAssistant) -> bool:
    """Carrega o card de alertas no frontend, sem passo manual no Lovelace.

    Equivale ao que já acontece com o plugin do mapa: a integração serve o
    arquivo e o disponibiliza sozinha. Usa a URL versionada para furar cache.
    Retorna False quando o frontend ainda não foi configurado.
    """
    # Import tardio: mantém o pacote leve para os testes unitários (sem HA)
    from homeassistant.components.frontend import (
        DATA_EXTRA_MODULE_URL,
        add_extra_js_url,
    )

    gerenciador = hass.data.get(DATA_EXTRA_MODULE_URL)
    if gerenciador is None:
        return False

    caminho = f"/{DOMAIN}/{CARD_ALERTAS_JS}"
    # Remove versões antigas (sem reiniciar o HA após um upgrade).
    for url in list(gerenciador.urls):
        if url.split("?", 1)[0] == caminho:
            gerenciador.remove(url)

    add_extra_js_url(hass, f"{caminho}?v={VERSION}")
    _LOGGER.debug("Card de alertas carregado no frontend: %s", caminho)
    return True


@callback
def _agendar_registro_card(hass: HomeAssistant) -> None:
    """Registra o card agora ou, se o frontend ainda não subiu, no start do HA."""
    if _registrar_card_no_frontend(hass):
        return

    chave = f"{DOMAIN}_card_registro_agendado"
    if hass.data.get(chave) or hass.is_running:
        _LOGGER.debug("Frontend indisponível; card de alertas não será carregado")
        return

    hass.data[chave] = True
    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STARTED,
        lambda _evento: _registrar_card_no_frontend(hass),
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configuração ao adicionar a integração pela interface."""
    # Import tardio: mantém o pacote leve para os testes unitários (sem HA)
    from .coordinator import INMETDataUpdateCoordinator

    estado = entry.data[CONF_ESTADO]
    update_interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    notificacoes_perigo = entry.options.get(
        CONF_NOTIFICACOES_PERIGO, DEFAULT_NOTIFICACOES_PERIGO
    )

    coordenador = INMETDataUpdateCoordinator(
        hass, entry, estado, update_interval, notificacoes_perigo
    )

    # Testa o setup de verdade: falha aqui → ConfigEntryNotReady + retry do HA
    await coordenador.async_config_entry_first_refresh()

    entry.runtime_data = coordenador

    _agendar_registro_card(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listener para opções: recarrega a entrada quando mudam
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove a integração."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Recarrega a entrada quando as opções são atualizadas."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migra entradas v1 → v2 (settings saem de `data` para `options`)."""
    if entry.version > 1:
        return True

    estado = entry.data.get(CONF_ESTADO)
    if not estado:
        _LOGGER.error(
            "Config entry %s não possui 'estado'; migração abortada", entry.entry_id
        )
        return False

    nova_data = {CONF_ESTADO: estado}
    novas_options = dict(entry.options)
    for chave in (CONF_NOTIFICACOES_PERIGO, CONF_UPDATE_INTERVAL):
        if chave in entry.data and chave not in novas_options:
            novas_options[chave] = entry.data[chave]

    hass.config_entries.async_update_entry(
        entry, data=nova_data, options=novas_options, version=2
    )
    _LOGGER.debug("Config entry %s migrada para a versão 2", entry.entry_id)
    return True
