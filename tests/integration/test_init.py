"""Testes de setup/unload e de migração de config entry."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.inmet_alertas import async_migrate_entry
from custom_components.inmet_alertas.const import (
    CONF_ESTADO,
    CONF_NOTIFICACOES_PERIGO,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    SERVICE_ATUALIZAR_ALERTAS,
)


async def test_migracao_v1_para_v2_move_settings_para_options(hass):
    """v1 (tudo em data) → v2 (estado em data, ajustes em options)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        unique_id=f"{DOMAIN}_SP",
        data={
            CONF_ESTADO: "SP",
            CONF_NOTIFICACOES_PERIGO: False,
            CONF_UPDATE_INTERVAL: 60,
        },
        options={},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True
    assert entry.version == 2
    assert entry.data == {CONF_ESTADO: "SP"}
    assert entry.options == {
        CONF_NOTIFICACOES_PERIGO: False,
        CONF_UPDATE_INTERVAL: 60,
    }


async def test_migracao_preserva_options_existentes(hass):
    """Options já definidas não são sobrescritas pela migração."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        unique_id=f"{DOMAIN}_RJ",
        data={CONF_ESTADO: "RJ", CONF_UPDATE_INTERVAL: 60},
        options={CONF_UPDATE_INTERVAL: 30},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True
    assert entry.options[CONF_UPDATE_INTERVAL] == 30


async def test_setup_cria_entidades_e_unload_marca_indisponivel(hass):
    """Setup cria os 4 sensores; unload os marca como unavailable (HA moderno)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=f"{DOMAIN}_GO",
        data={CONF_ESTADO: "GO"},
        options={CONF_NOTIFICACOES_PERIGO: True, CONF_UPDATE_INTERVAL: 45},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.inmet_alertas.coordinator."
        "INMETDataUpdateCoordinator.async_config_entry_first_refresh",
        new_callable=AsyncMock,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert len(hass.states.async_entity_ids("sensor")) == 4

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    # Entidades registradas permanecem no state machine como `unavailable`
    for entity_id in hass.states.async_entity_ids("sensor"):
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_servico_atualizar_alertas_valida_estado(hass):
    """Serviço: dispara refresh no estado configurado e valida a entrada."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=f"{DOMAIN}_GO",
        data={CONF_ESTADO: "GO"},
        options={},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.inmet_alertas.coordinator."
        "INMETDataUpdateCoordinator.async_config_entry_first_refresh",
        new_callable=AsyncMock,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    with patch(
        "custom_components.inmet_alertas.coordinator."
        "INMETDataUpdateCoordinator.async_request_refresh",
        new_callable=AsyncMock,
    ) as mock_refresh:
        await hass.services.async_call(
            DOMAIN, SERVICE_ATUALIZAR_ALERTAS, {}, blocking=True
        )
        mock_refresh.assert_awaited_once()

    # Estado válido, mas não configurado → ServiceValidationError
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, SERVICE_ATUALIZAR_ALERTAS, {CONF_ESTADO: "RJ"}, blocking=True
        )

    # Estado fora do schema → inválido na própria validação do serviço
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN, SERVICE_ATUALIZAR_ALERTAS, {CONF_ESTADO: "XX"}, blocking=True
        )


async def test_entidades_ficam_indisponiveis_quando_ciclo_falha(hass):
    """entity-unavailable: falha no coordenador deixa as entidades unavailable."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=f"{DOMAIN}_GO",
        data={CONF_ESTADO: "GO"},
        options={},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.inmet_alertas.coordinator."
        "INMETDataUpdateCoordinator.async_config_entry_first_refresh",
        new_callable=AsyncMock,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "sensor.quantidade_de_alertas_go"

    coordenador = entry.runtime_data
    coordenador.last_update_success = False
    coordenador.async_update_listeners()
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_servico_erro_interno_levanta_home_assistant_error(hass):
    """action-exceptions: falha de execução do serviço → HomeAssistantError."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=f"{DOMAIN}_GO",
        data={CONF_ESTADO: "GO"},
        options={},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.inmet_alertas.coordinator."
        "INMETDataUpdateCoordinator.async_config_entry_first_refresh",
        new_callable=AsyncMock,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    with patch.object(
        type(entry.runtime_data),
        "async_request_refresh",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                DOMAIN, SERVICE_ATUALIZAR_ALERTAS, {}, blocking=True
            )
