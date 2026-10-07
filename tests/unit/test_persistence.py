"""Testes unitários do merge/expiração de alertas persistentes (lógica pura)."""
from datetime import datetime, timedelta, timezone

from custom_components.inmet_alertas.helpers.persistence import (
    alerta_ainda_valido,
    mesclar_alertas,
)

AGORA = datetime(2026, 10, 7, 12, 0, tzinfo=timezone(timedelta(hours=-3)))


# --- alerta_ainda_valido ---


def test_valido_quando_expira_no_futuro():
    assert (
        alerta_ainda_valido({"expires": "2026-10-08T18:00:00-03:00"}, AGORA) is True
    )


def test_invalido_quando_expira_no_passado():
    assert (
        alerta_ainda_valido({"expires": "2026-10-06T18:00:00-03:00"}, AGORA) is False
    )


def test_valido_sem_datas():
    assert alerta_ainda_valido({}, AGORA) is True


def test_valido_com_formato_brasileiro_em_fim():
    """`fim` formatado (dd/mm/aaaa) não é ISO: assume válido."""
    assert alerta_ainda_valido({"fim": "07/10/2026 18:00"}, AGORA) is True


def test_valido_com_sufixo_z():
    assert alerta_ainda_valido({"expires": "2026-10-08T18:00:00Z"}, AGORA) is True
    assert alerta_ainda_valido({"expires": "2026-10-06T18:00:00Z"}, AGORA) is False


def test_valido_quando_iso_invalido():
    assert alerta_ainda_valido({"expires": "2026-13-40T99:99:00-03:00"}, AGORA) is True


def test_usa_fim_quando_expires_ausente():
    assert alerta_ainda_valido({"fim": "2026-10-08T18:00:00-03:00"}, AGORA) is True
    assert alerta_ainda_valido({"fim": "2026-10-06T18:00:00-03:00"}, AGORA) is False


# --- mesclar_alertas ---


def test_merge_mantem_remove_adiciona_e_atualiza():
    persistentes = {
        "VIVO": {
            "id": "VIVO",
            "titulo": "antigo",
            "expires": "2026-10-08T18:00:00-03:00",
        },
        "EXPIRADO": {"id": "EXPIRADO", "expires": "2026-10-01T18:00:00-03:00"},
    }
    novos = [
        {"id": "VIVO", "titulo": "atualizado"},
        {"id": "NOVO", "titulo": "novo"},
    ]

    lista, cache = mesclar_alertas(persistentes, novos, AGORA)

    assert [a["id"] for a in lista] == ["VIVO", "NOVO"]
    assert cache["VIVO"]["titulo"] == "atualizado"
    assert "EXPIRADO" not in cache


def test_merge_sem_prazo_mantem_alerta():
    persistentes = {"SEMPRAZO": {"id": "SEMPRAZO", "titulo": "permanente"}}
    lista, cache = mesclar_alertas(persistentes, [], AGORA)
    assert [a["id"] for a in lista] == ["SEMPRAZO"]
    assert cache["SEMPRAZO"]["titulo"] == "permanente"


def test_merge_nao_muta_dicts_originais():
    persistentes = {"A1": {"id": "A1", "titulo": "antigo"}}
    novos = [{"id": "A1", "titulo": "novo"}]
    mesclar_alertas(persistentes, novos, AGORA)
    assert persistentes["A1"]["titulo"] == "antigo"
