"""Testes de setup/unload e de migraÃ§Ã£o de config entry."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import voluptuous as vol
from homeassistant.components.lovelace.const import DOMAIN as LOVELACE_DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.inmet_alertas import (
    _async_registrar_recurso_lovelace,
    async_migrate_entry,
)
from custom_components.inmet_alertas.const import (
    CONF_ESTADO,
    CONF_NOTIFICACOES_PERIGO,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    SERVICE_ATUALIZAR_ALERTAS,
    URL_RSS,
)


async def test_migracao_v1_para_v2_move_settings_para_options(hass):
    """v1 (tudo em data) â†’ v2 (estado em data, ajustes em options)."""
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
    """Options jÃ¡ definidas nÃ£o sÃ£o sobrescritas pela migraÃ§Ã£o."""
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
    """ServiÃ§o: dispara refresh no estado configurado e valida a entrada."""
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
        "INMETDataUpdateCoordinator.async_refresh",
        new_callable=AsyncMock,
    ) as mock_refresh:
        await hass.services.async_call(
            DOMAIN, SERVICE_ATUALIZAR_ALERTAS, {}, blocking=True
        )
        mock_refresh.assert_awaited_once()

    # Estado vÃ¡lido, mas nÃ£o configurado â†’ ServiceValidationError
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, SERVICE_ATUALIZAR_ALERTAS, {CONF_ESTADO: "RJ"}, blocking=True
        )

    # Estado fora do schema â†’ invÃ¡lido na prÃ³pria validaÃ§Ã£o do serviÃ§o
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
    """action-exceptions: falha de execuÃ§Ã£o do serviÃ§o â†’ HomeAssistantError."""
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
        "async_refresh",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                DOMAIN, SERVICE_ATUALIZAR_ALERTAS, {}, blocking=True
            )


async def test_migracao_entry_corrompida_retorna_false(hass):
    """Entry v1 sem 'estado' â†’ migraÃ§Ã£o aborta (False); o HA reconfigura."""
    entry = MockConfigEntry(domain=DOMAIN, version=1, data={}, options={})
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is False
    assert entry.version == 1


async def test_migracao_entry_ja_v2_nao_altera_dados(hass):
    """Entry jÃ¡ na versÃ£o 2 â†’ migraÃ§Ã£o Ã© no-op e preserva data/options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=f"{DOMAIN}_SP",
        data={CONF_ESTADO: "SP"},
        options={CONF_UPDATE_INTERVAL: 30},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True
    assert entry.data == {CONF_ESTADO: "SP"}
    assert entry.options == {CONF_UPDATE_INTERVAL: 30}
    assert entry.version == 2


async def test_setup_falha_no_feed_gera_setup_retry(hass, aioclient_mock):
    """test-before-setup: feed fora do ar â†’ ConfigEntryNotReady + retry do HA."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=f"{DOMAIN}_GO",
        data={CONF_ESTADO: "GO"},
        options={},
    )
    entry.add_to_hass(hass)

    aioclient_mock.get(URL_RSS, status=500)

    assert await hass.config_entries.async_setup(entry.entry_id) is False
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_card_de_alertas_carregado_automaticamente(hass):
    """O card Ã© registrado como recurso do Lovelace sozinho (sem passo manual)."""

    class RecursosStub:
        def __init__(self):
            self.itens = []
            self.criados = []
            self.atualizados = []

        async def async_get_info(self):
            return {"resources": len(self.itens)}

        def async_items(self):
            return list(self.itens)

        async def async_create_item(self, data):
            self.criados.append(data)
            item = {**data, "id": f"id{len(self.itens)}"}
            self.itens.append(item)
            return item

        async def async_update_item(self, item_id, updates):
            self.atualizados.append((item_id, updates))
            for item in self.itens:
                if item["id"] == item_id:
                    item.update(updates)
            return item

    recursos = RecursosStub()
    hass.data[LOVELACE_DOMAIN] = type("Lovelace", (), {"resources": recursos})()

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

    assert recursos.criados == [
        {"res_type": "module", "url": "/inmet_alertas/inmet-alert-card.js?v=2.0.1"}
    ]
    assert recursos.atualizados == []


async def test_card_de_alertas_atualiza_recurso_existente(hass):
    """VersÃ£o nova atualiza a URL do recurso em vez de duplicar."""

    class RecursosStub:
        def __init__(self):
            self.itens = [
                {
                    "id": "abc",
                    "type": "module",
                    "url": "/inmet_alertas/inmet-alert-card.js?v=1.0.0",
                }
            ]
            self.criados = []
            self.atualizados = []

        async def async_get_info(self):
            return {"resources": len(self.itens)}

        def async_items(self):
            return list(self.itens)

        async def async_create_item(self, data):
            self.criados.append(data)

        async def async_update_item(self, item_id, updates):
            self.atualizados.append((item_id, updates))
            for item in self.itens:
                if item["id"] == item_id:
                    item.update(updates)

    recursos = RecursosStub()
    hass.data[LOVELACE_DOMAIN] = type("Lovelace", (), {"resources": recursos})()

    assert await _async_registrar_recurso_lovelace(hass) is True
    assert recursos.criados == []
    assert recursos.atualizados == [
        ("abc", {"url": "/inmet_alertas/inmet-alert-card.js?v=2.0.1"})
    ]


async def test_card_de_alertas_sem_lovelace_nao_quebra(hass):
    """Sem Lovelace (ou modo YAML) a integraÃ§Ã£o segue normalmente."""
    hass.data.pop(LOVELACE_DOMAIN, None)
    assert await _async_registrar_recurso_lovelace(hass) is False
