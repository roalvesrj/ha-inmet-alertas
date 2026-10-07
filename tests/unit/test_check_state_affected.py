"""Testes para check_state_affected e filter_state_municipalities."""
from custom_components.inmet_alertas.const import MICRORREGIOES_ESTADOS
from custom_components.inmet_alertas.utils import (
    check_state_affected,
    filter_state_municipalities,
)


def test_afeta_por_municipio_rj():
    cap = {"municipios": "Rio de Janeiro - RJ (3304557), Niterói - RJ (3303302)"}
    assert check_state_affected(cap, "RJ") is True


def test_afeta_por_municipio_sp():
    cap = {"municipios": "São Paulo - SP (3550308), Campinas - SP (3509502)"}
    assert check_state_affected(cap, "SP") is True


def test_nao_afeta_outro_estado():
    cap = {"municipios": "São Paulo - SP (3550308)"}
    assert check_state_affected(cap, "RJ") is False


def test_afeta_por_microrregiao():
    cap = {"municipios": "Metropolitana do Rio de Janeiro"}
    assert check_state_affected(cap, "RJ") is True


def test_nao_afeta_sem_municipios():
    cap = {"municipios": ""}
    assert check_state_affected(cap, "RJ") is False


def test_nao_afeta_sem_campo():
    cap = {}
    assert check_state_affected(cap, "RJ") is False


def test_sem_estado_retorna_true():
    cap = {"municipios": "Rio de Janeiro - RJ (3304557)"}
    assert check_state_affected(cap, "") is True


def test_estado_tag_formatada():
    cap = {"municipios": "Rio de Janeiro - RJ (3304557)"}
    assert check_state_affected(cap, "RJ") is True


def test_estado_tag_sem_espaco():
    cap = {"municipios": "Rio de Janeiro - RJ (3304557)"}
    assert check_state_affected(cap, "RJ") is True


def test_microrregiao_todas_rj():
    for nome, estado in MICRORREGIOES_ESTADOS.items():
        if estado == "RJ":
            cap = {"municipios": nome}
            assert check_state_affected(cap, "RJ") is True, f"Microrregião {nome} deveria afetar RJ"


def test_microrregiao_nao_afeta_outro_estado():
    for nome, estado in MICRORREGIOES_ESTADOS.items():
        if estado != "SP":
            cap = {"municipios": nome}
            if check_state_affected(cap, "SP"):
                assert estado == "SP", f"{nome} pertence a {estado}, não a SP"


def test_filter_municipios_rj():
    cap = {"municipios": "Rio de Janeiro - RJ (3304557), Niterói - RJ (3303302), São Paulo - SP (3550308)"}
    result = filter_state_municipalities(cap["municipios"], "RJ")
    assert len(result) == 2
    assert all("RJ" in m for m in result)


def test_filter_municipios_sem_correspondencia():
    result = filter_state_municipalities("São Paulo - SP (3550308)", "RJ")
    assert result == []


def test_filter_municipios_vazio():
    assert filter_state_municipalities("", "RJ") == []
