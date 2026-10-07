"""Fixtures dos testes de integração (harness do Home Assistant)."""
from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Habilita a integração customizada em todos os testes."""
    yield


@pytest.fixture(name="mock_setup_entry")
def mock_setup_entry_fixture():
    """Evita o setup real (rede) quando o fluxo cria a config entry."""
    with patch("custom_components.inmet_alertas.async_setup_entry", return_value=True):
        yield


@pytest.fixture(name="mock_feed")
def mock_feed_fixture():
    """Mocka a verificação de conectividade do feed no config flow."""
    with patch(
        "custom_components.inmet_alertas.config_flow.async_verificar_feed",
        return_value=True,
    ) as mock:
        yield mock
