"""Testes unitários dos utilitários de data (lógica pura)."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.util import dt as dt_util

from custom_components.inmet_alertas.utils import format_datetime, is_alert_active


def test_format_datetime_vazio():
    assert format_datetime("") == ""
    assert format_datetime(None) == ""


def test_format_datetime_formata_para_brasileiro():
    """Data no fuso local do HA sai em dd/mm/aaaa HH:MM."""
    local = dt_util.now().replace(microsecond=0)
    assert format_datetime(local.isoformat()) == local.strftime("%d/%m/%Y %H:%M")


def test_format_datetime_invalido_devolve_original():
    assert format_datetime("nao-e-data") == "nao-e-data"


def test_is_alert_active_dentro_do_periodo():
    agora = dt_util.now()
    cap = {
        "onset": (agora - timedelta(hours=1)).isoformat(),
        "expires": (agora + timedelta(hours=1)).isoformat(),
    }
    assert is_alert_active(cap, agora) is True


def test_is_alert_active_fora_do_periodo():
    agora = dt_util.now()
    cap = {
        "onset": (agora - timedelta(hours=3)).isoformat(),
        "expires": (agora - timedelta(hours=1)).isoformat(),
    }
    assert is_alert_active(cap, agora) is False


def test_is_alert_active_sem_datas_conta_ativo():
    assert is_alert_active({}, dt_util.now()) is True


def test_is_alert_active_data_invalida_conta_ativo():
    cap = {"onset": "lixo", "expires": "lixo"}
    assert is_alert_active(cap, dt_util.now()) is True
