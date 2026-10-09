"""Testes do coordenador: indisponibilidade, recuperação e parsing básico."""
from __future__ import annotations

import logging

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.inmet_alertas.const import CONF_ESTADO, DOMAIN, URL_RSS
from custom_components.inmet_alertas.coordinator import INMETDataUpdateCoordinator

RSS_VAZIO = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>INMET</title></channel></rss>"""

LOGGER_COORDENADOR = "custom_components.inmet_alertas.coordinator"


def _criar_coordenador(hass) -> INMETDataUpdateCoordinator:
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_ESTADO: "GO"})
    entry.add_to_hass(hass)
    return INMETDataUpdateCoordinator(hass, entry, "GO", 45, True)


async def test_update_registra_indisponibilidade_uma_vez(hass, aioclient_mock, caplog):
    """Falha no feed: loga indisponível uma vez e levanta UpdateFailed."""
    coordenador = _criar_coordenador(hass)
    aioclient_mock.get(URL_RSS, status=500)

    with caplog.at_level(logging.WARNING, logger=LOGGER_COORDENADOR):
        with pytest.raises(UpdateFailed):
            await coordenador._async_update_data()
        with pytest.raises(UpdateFailed):
            await coordenador._async_update_data()

    assert caplog.text.count("INMET indisponível") == 1
    assert coordenador._indisponivel_logado is True


async def test_update_recupera_e_registra_volta(hass, aioclient_mock, caplog):
    """Após falha, sucesso loga a recuperação e volta todos os dados."""
    coordenador = _criar_coordenador(hass)

    aioclient_mock.get(URL_RSS, status=500)
    with pytest.raises(UpdateFailed):
        await coordenador._async_update_data()

    aioclient_mock.clear_requests()
    aioclient_mock.get(URL_RSS, text=RSS_VAZIO)

    with caplog.at_level(logging.INFO, logger=LOGGER_COORDENADOR):
        dados = await coordenador._async_update_data()

    assert dados["count"] == 0
    assert dados["estado"] == "GO"
    assert coordenador._indisponivel_logado is False
    assert "INMET voltou a responder" in caplog.text


async def test_update_aceita_feed_sem_items(hass, aioclient_mock):
    """Feed vazio não deve quebrar o parsing (regressão: 'invalid predicate')."""
    coordenador = _criar_coordenador(hass)
    aioclient_mock.get(URL_RSS, text=RSS_VAZIO)

    dados = await coordenador._async_update_data()

    assert dados["count"] == 0


async def test_update_aceita_feed_em_namespace(hass, aioclient_mock):
    """Feed Atom (com namespace) usa o fallback de busca de items."""
    feed_atom = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><title>Alerta</title></entry>
</feed>"""
    coordenador = _criar_coordenador(hass)
    aioclient_mock.get(URL_RSS, text=feed_atom)

    dados = await coordenador._async_update_data()

    assert dados["count"] == 0
