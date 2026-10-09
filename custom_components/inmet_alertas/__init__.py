"""Integração INMET Alertas para Home Assistant."""
from __future__ import annotations

import logging
from pathlib import Path

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_ESTADO,
    CONF_NOTIFICACOES_PERIGO,
    CONF_UPDATE_INTERVAL,
    DEFAULT_NOTIFICACOES_PERIGO,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    ESTADOS_BRASILEIROS,
    SERVICE_ATUALIZAR_ALERTAS,
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
                await coordenador.async_request_refresh()
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

    return True


async def _async_registrar_recurso_estatico(hass: HomeAssistant) -> None:
    """Registra /hacsfiles/<domain> → www/ para o plugin de mapa."""
    if hass.http is None:
        _LOGGER.debug("HTTP indisponível; plugin de mapa não será servido")
        return

    # Import tardio: mantém o pacote leve para os testes unitários (sem HA)
    from homeassistant.components.http import StaticPathConfig

    # Caminho relativo ao próprio módulo (robusto p/ qualquer diretório de config)
    plugin_path = Path(__file__).parent / "www"
    if not plugin_path.is_dir():
        _LOGGER.warning("Pasta do plugin não encontrada: %s", plugin_path)
        return

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(f"/hacsfiles/{DOMAIN}", str(plugin_path), False)]
        )
    except RuntimeError:
        # Rota já registrada (ex.: outro reload no mesmo processo)
        _LOGGER.debug("Recurso estático já registrado para %s", DOMAIN)
    else:
        _LOGGER.info(
            "✅ Plugin INMET disponível em: /hacsfiles/%s/plugin_inmet_polygons.js",
            DOMAIN,
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
