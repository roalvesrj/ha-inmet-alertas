"""Testes dos sensores: estado, atributos e a regra 'não mentir estado'."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.const import STATE_UNKNOWN
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.inmet_alertas.const import CONF_ESTADO, DOMAIN

ALERTA = {
    "id": "A1",
    "titulo": "Chuvas Intensas",
    "severidade": "Perigo",
    "evento": "Chuva",
    "inicio": "07/10/2026 10:00",
    "fim": "07/10/2026 18:00",
    "municipios_estado": ["Goiânia - GO"],
}


async def _setup(hass, dados):
    """Sobe a entrada com o primeiro refresh mockado e injeta dados no coordenador."""
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

    coordenador = entry.runtime_data
    coordenador.data = dados
    coordenador.async_update_listeners()
    await hass.async_block_till_done()
    return coordenador


async def test_sensores_refletem_os_alertas(hass):
    """Com dados: título, contagem, mapa (polígonos) e diagnóstico ok."""
    alerta = dict(ALERTA, dados_geograficos={"poligonos_individuais": [{}, {}]})
    await _setup(
        hass,
        {
            "alerts": [alerta],
            "count": 1,
            "estado": "GO",
            "last_update": "2026-10-07T12:00:00-03:00",
            "diagnostico": {"ultimo_http_status": 200, "rate_limit_hits": 0},
        },
    )

    assert hass.states.get("sensor.alertas_meteorologicos_go").state == "Chuvas Intensas"
    assert hass.states.get("sensor.quantidade_de_alertas_go").state == "1"
    assert hass.states.get("sensor.inmet_alertas_mapa_go").state == "2"
    assert hass.states.get("sensor.diagnostico_inmet_go").state == "ok"


async def test_sem_alertas_mostra_resumo_honesto(hass):
    """Feed ok sem alertas: 'Nenhum alerta ativo' (os dados existem)."""
    await _setup(
        hass,
        {
            "alerts": [],
            "count": 0,
            "estado": "GO",
            "diagnostico": {"ultimo_http_status": 200},
        },
    )

    assert (
        hass.states.get("sensor.alertas_meteorologicos_go").state
        == "Nenhum alerta ativo"
    )
    assert hass.states.get("sensor.quantidade_de_alertas_go").state == "0"


async def test_sem_dados_nao_mente_estado(hass):
    """Regra 'não mentir estado': sem dados os sensores ficam unknown."""
    await _setup(hass, None)

    for entity_id in (
        "sensor.alertas_meteorologicos_go",
        "sensor.quantidade_de_alertas_go",
        "sensor.inmet_alertas_mapa_go",
        "sensor.diagnostico_inmet_go",
    ):
        assert hass.states.get(entity_id).state == STATE_UNKNOWN
