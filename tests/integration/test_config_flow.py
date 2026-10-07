"""Testes do config flow e do options flow.

O Bronze exige 100% de cobertura do `config_flow.py` — os cenários aqui
cobrem: formulário, happy path com defaults, erro + recuperação, duplicata,
estado inválido (via schema e por chamada direta) e opções.
"""
from __future__ import annotations

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.inmet_alertas.config_flow import InmetAlertasConfigFlow
from custom_components.inmet_alertas.const import (
    CONF_ESTADO,
    CONF_NOTIFICACOES_PERIGO,
    CONF_UPDATE_INTERVAL,
    DEFAULT_NOTIFICACOES_PERIGO,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)


async def _iniciar_flow(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}
    return result


async def test_formulario_inicial(hass):
    """O passo inicial mostra o formulário sem erros."""
    await _iniciar_flow(hass)


async def test_fluxo_completo_cria_entry_com_defaults(
    hass, mock_setup_entry, mock_feed
):
    """Happy path: estado válido + feed acessível → entry com defaults."""
    result = await _iniciar_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ESTADO: "SP"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "INMET Alertas - São Paulo"
    assert result["data"] == {CONF_ESTADO: "SP"}
    assert result["options"] == {
        CONF_NOTIFICACOES_PERIGO: DEFAULT_NOTIFICACOES_PERIGO,
        CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
    }
    assert result["result"].unique_id == f"{DOMAIN}_SP"


async def test_estado_invalido_direto(hass):
    """Validação defensiva do estado (schema do form não deixa passar)."""
    flow = InmetAlertasConfigFlow()
    flow.hass = hass
    flow.flow_id = "teste"
    flow.handler = DOMAIN
    flow.context = {"source": config_entries.SOURCE_USER}

    result = await flow.async_step_user({CONF_ESTADO: "XX"})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_ESTADO: "invalid_state"}


async def test_estado_invalido_via_manager(hass):
    """Estado fora do schema: o manager rejeita com InvalidData."""
    result = await _iniciar_flow(hass)

    with pytest.raises(InvalidData):
        await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_ESTADO: "XX"}
        )


async def test_duplicado_aborta(hass, mock_setup_entry, mock_feed):
    """Mesmo estado já configurado → abort already_configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{DOMAIN}_SP",
        data={CONF_ESTADO: "SP"},
    )
    entry.add_to_hass(hass)

    result = await _iniciar_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ESTADO: "SP"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_cannot_connect_e_recuperacao(hass, mock_setup_entry, mock_feed):
    """Feed fora do ar mostra erro; a próxima tentativa conclui o fluxo."""
    mock_feed.return_value = False

    result = await _iniciar_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ESTADO: "SP"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Recuperação: feed volta e o usuário reenvia o formulário
    mock_feed.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ESTADO: "SP"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_erro_inesperado(hass, mock_setup_entry, mock_feed):
    """Exceção inesperada na checagem → erro 'unknown' no formulário."""
    mock_feed.side_effect = RuntimeError("boom")

    result = await _iniciar_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ESTADO: "RJ"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_options_flow_salva(hass):
    """Options flow mostra o form e persiste os ajustes."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=f"{DOMAIN}_MG",
        data={CONF_ESTADO: "MG"},
        options={CONF_NOTIFICACOES_PERIGO: True, CONF_UPDATE_INTERVAL: 45},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_NOTIFICACOES_PERIGO: False, CONF_UPDATE_INTERVAL: 60},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_NOTIFICACOES_PERIGO: False,
        CONF_UPDATE_INTERVAL: 60,
    }
    assert entry.options == {
        CONF_NOTIFICACOES_PERIGO: False,
        CONF_UPDATE_INTERVAL: 60,
    }
