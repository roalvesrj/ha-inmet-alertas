"""Testes unitários da montagem de atributos dos sensores (lógica pura)."""
from custom_components.inmet_alertas.helpers.sensor_data import (
    calcular_resumo,
    construir_atributos_mapa,
    preparar_alertas_para_atributos,
)

BBOX_RJ = {"min_lat": -23.0, "max_lat": -22.9, "min_lon": -43.3, "max_lon": -43.2}


def _poligono(area=100.0, centro=None, bbox=None):
    return {
        "coordenadas": [
            [-22.9, -43.2],
            [-22.9, -43.3],
            [-23.0, -43.3],
            [-22.9, -43.2],
        ],
        "area_km2": area,
        "centro": centro or [-22.95, -43.25],
        "bounding_box": bbox or BBOX_RJ,
    }


def _alerta(
    alert_id="A1",
    severidade="Perigo",
    evento="Chuva",
    descricao="Descrição X",
    com_geo=True,
    municipios=None,
):
    alerta = {
        "id": alert_id,
        "titulo": f"Alerta {alert_id}",
        "evento": evento,
        "severidade": severidade,
        "color_risk": "#FF8C00",
        "onset": "2026-10-01T10:00:00-03:00",
        "expires": "2026-10-08T18:00:00-03:00",
        "descricao": descricao,
        "municipios_estado": (
            municipios if municipios is not None else ["Rio de Janeiro - RJ (3304557)"]
        ),
    }
    if com_geo:
        alerta["dados_geograficos"] = {
            "poligonos_individuais": [_poligono()],
            "area_total_km2": 100.0,
            "centro_geografico": [-22.95, -43.25],
            "bounding_box": BBOX_RJ,
            "zoom_recomendado": 10,
            "total_poligonos": 1,
        }
    return alerta


# --- regressão M1: polígonos devem expor evento e descrição ---


def test_poligono_inclui_evento_e_descricao():
    """Regressão: `evento`/`descricao` ficavam vazios por leitura com chave errada."""
    attrs = construir_atributos_mapa("RJ", [_alerta()], "2026-10-07T12:00:00-03:00")
    poligono = attrs["poligonos"][0]
    assert poligono["evento"] == "Chuva"
    assert poligono["descricao"] == "Descrição X"


# --- atributos do mapa ---


def test_atributos_mapa_vazio():
    attrs = construir_atributos_mapa("RJ", [], None)
    assert attrs["estado"] == "RJ"
    assert attrs["poligonos"] == []
    assert attrs["area_total_afetada_km2"] == 0.0
    assert attrs["centro_geografico"] is None
    assert attrs["bounding_box"] is None
    assert attrs["zoom_recomendado"] == 8
    assert attrs["camadas_por_severidade"] == {}
    assert attrs["total_alertas_com_geo"] == 0
    assert attrs["ultima_atualizacao"] is None


def test_poligonos_ordenados_por_severidade():
    alertas = [
        _alerta("A1", "Perigo Potencial"),
        _alerta("A2", "Grande Perigo"),
        _alerta("A3", "Perigo"),
    ]
    attrs = construir_atributos_mapa("RJ", alertas, None)
    severidades = [p["severidade"] for p in attrs["poligonos"]]
    assert severidades == ["Grande Perigo", "Perigo", "Perigo Potencial"]


def test_agregacao_area_centro_bbox_e_camadas():
    a1 = _alerta("A1")
    a2 = _alerta("A2")
    bbox_sp = {"min_lat": -22.1, "max_lat": -21.9, "min_lon": -43.1, "max_lon": -42.9}
    a2["dados_geograficos"]["poligonos_individuais"] = [
        _poligono(area=50.0, centro=[-22.0, -43.0], bbox=bbox_sp)
    ]
    a2["dados_geograficos"]["area_total_km2"] = 50.0
    a2["dados_geograficos"]["centro_geografico"] = [-22.0, -43.0]
    a2["dados_geograficos"]["bounding_box"] = bbox_sp

    attrs = construir_atributos_mapa("RJ", [a1, a2], "2026-10-07T12:00:00-03:00")

    assert attrs["area_total_afetada_km2"] == 150.0
    assert attrs["bounding_box"] == {
        "min_lat": -23.0,
        "max_lat": -21.9,
        "min_lon": -43.3,
        "max_lon": -42.9,
    }
    assert attrs["centro_geografico"][0] == -22.475
    assert attrs["centro_geografico"][1] == -43.125
    assert attrs["total_alertas_com_geo"] == 2
    camada = attrs["camadas_por_severidade"]["Perigo"]
    assert camada["total_poligonos"] == 2
    assert camada["area_total_km2"] == 150.0


def test_alerta_sem_geometria_nao_entra_no_mapa():
    attrs = construir_atributos_mapa("RJ", [_alerta(com_geo=False)], None)
    assert attrs["poligonos"] == []
    assert attrs["total_alertas_com_geo"] == 0


# --- sensor principal ---


def test_preparar_alertas_remove_geometria_sem_mutar_original():
    original = _alerta()
    resultado = preparar_alertas_para_atributos([original])
    assert "dados_geograficos" not in resultado[0]
    assert "dados_geograficos" in original
    assert resultado[0]["evento"] == "Chuva"


def test_calcular_resumo():
    alertas = [
        _alerta(
            "A1",
            "Perigo",
            municipios=["Rio de Janeiro - RJ (3304557)", "Niterói - RJ (3303302)"],
        ),
        _alerta("A2", "Grande Perigo", municipios=["Niterói - RJ (3303302)"]),
    ]
    resumo = calcular_resumo(alertas)
    assert resumo["alertas_por_severidade"] == {"Perigo": 1, "Grande Perigo": 1}
    assert resumo["severidade_maxima"] == "Grande Perigo"
    assert resumo["municipios_unicos"] == 2
    assert resumo["municipios_afetados"] == [
        "Niterói - RJ (3303302)",
        "Rio de Janeiro - RJ (3304557)",
    ]


def test_calcular_resumo_vazio():
    resumo = calcular_resumo([])
    assert resumo["alertas_por_severidade"] == {}
    assert resumo["severidade_maxima"] is None
    assert resumo["municipios_unicos"] == 0
    assert resumo["municipios_afetados"] == []
