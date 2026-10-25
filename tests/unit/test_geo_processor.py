"""Testes para o GeoProcessor."""
import pytest

from custom_components.inmet_alertas.helpers.geo_processor import GeoProcessor


@pytest.fixture
def processor():
    return GeoProcessor()


def test_parse_coordenadas_none(processor):
    assert processor.parse_coordenadas_cap(None) is None


def test_parse_coordenadas_empty(processor):
    assert processor.parse_coordenadas_cap("") is None


def test_parse_coordenadas_simples(processor):
    coords = processor.parse_coordenadas_cap("-22.9,-43.2 -22.9,-43.3 -23.0,-43.3 -23.0,-43.2 -22.9,-43.2")
    assert coords is not None
    assert len(coords) >= 4
    assert coords[0] == [-22.9, -43.2]
    # Should be closed polygon
    assert coords[0] == coords[-1]


def test_parse_coordenadas_dois_pontos(processor):
    coords = processor.parse_coordenadas_cap("-22.9,-43.2 -23.0,-43.3")
    assert coords is None


def test_parse_coordenadas_fora_do_brasil(processor):
    coords = processor.parse_coordenadas_cap("40.0,-100.0 41.0,-101.0 42.0,-102.0")
    assert coords is None


def test_centro_geografico_normal(processor):
    coords = [[-22.9, -43.2], [-22.9, -43.3], [-23.0, -43.3], [-23.0, -43.2], [-22.9, -43.2]]
    centro = processor.calcular_centro_geografico(coords)
    assert centro is not None
    assert abs(centro[0] - (-22.95)) < 0.01
    assert abs(centro[1] - (-43.25)) < 0.01


def test_centro_geografico_vazio(processor):
    assert processor.calcular_centro_geografico([]) is None


def test_centro_geografico_menos_de_3(processor):
    assert processor.calcular_centro_geografico([[-22.9, -43.2], [-23.0, -43.3]]) is None


def test_area_poligono_vazio(processor):
    assert processor.calcular_area_poligono([]) == 0.0


def test_area_poligono_menos_de_3(processor):
    assert processor.calcular_area_poligono([[-22.9, -43.2], [-23.0, -43.3]]) == 0.0


def test_area_poligono_quadrado(processor):
    coords = [[-22.9, -43.2], [-22.9, -43.3], [-23.0, -43.3], [-23.0, -43.2], [-22.9, -43.2]]
    area = processor.calcular_area_poligono(coords)
    assert area > 0


def test_bounding_box(processor):
    coords = [[-22.9, -43.2], [-22.9, -43.3], [-23.0, -43.3], [-23.0, -43.2]]
    bbox = processor.calcular_bounding_box(coords)
    assert bbox is not None
    assert bbox["min_lat"] == -23.0
    assert bbox["max_lat"] == -22.9
    assert bbox["min_lon"] == -43.3
    assert bbox["max_lon"] == -43.2


def test_bounding_box_vazia(processor):
    assert processor.calcular_bounding_box([]) is None


def test_zoom_recomendado_padrao(processor):
    assert processor.calcular_zoom_recomendado(None) == 8


def test_processar_poligono_completo(processor):
    """Pipeline completa: coordenadas → área, centro, bbox e zoom."""
    resultado = processor.processar_poligono_completo(
        "-22.9,-43.2 -22.9,-43.3 -23.0,-43.3 -23.0,-43.2 -22.9,-43.2", "A1"
    )

    assert resultado is not None
    assert resultado["area_km2"] > 0
    assert resultado["total_pontos"] == 4  # exclui o ponto de fechamento
    assert resultado["centro"] is not None
    assert resultado["bounding_box"]["min_lat"] == -23.0
    assert resultado["zoom_recomendado"] >= 8


def test_processar_poligono_completo_invalido(processor):
    """Texto inválido ou fora do Brasil → None (sem estourar)."""
    assert processor.processar_poligono_completo("abc", "A1") is None
    assert (
        processor.processar_poligono_completo(
            "40.0,-100.0 41.0,-101.0 42.0,-102.0", "A1"
        )
        is None
    )


def test_combinar_poligonos_estado_vazio(processor):
    """Sem polígonos: resultado padrão, sem centro e zoom 8."""
    resultado = processor.combinar_poligonos_estado([])

    assert resultado["total_poligonos"] == 0
    assert resultado["area_total_km2"] == 0.0
    assert resultado["centro_estado"] is None
    assert resultado["zoom_estado"] == 8


def test_combinar_poligonos_estado_pondera_centro_por_area(processor):
    """Centro ponderado pela área e bounding box agregado."""
    poligonos = [
        {
            "area_km2": 100.0,
            "centro": [-22.0, -43.0],
            "bounding_box": {
                "min_lat": -22.5,
                "max_lat": -21.5,
                "min_lon": -43.5,
                "max_lon": -42.5,
            },
        },
        {
            "area_km2": 300.0,
            "centro": [-23.0, -44.0],
            "bounding_box": {
                "min_lat": -23.5,
                "max_lat": -22.5,
                "min_lon": -44.5,
                "max_lon": -43.5,
            },
        },
    ]

    resultado = processor.combinar_poligonos_estado(poligonos)

    assert resultado["total_poligonos"] == 2
    assert resultado["area_total_km2"] == 400.0
    # (100*-22 + 300*-23)/400 = -22.75 ; (100*-43 + 300*-44)/400 = -43.75
    assert abs(resultado["centro_estado"][0] - (-22.75)) < 0.001
    assert abs(resultado["centro_estado"][1] - (-43.75)) < 0.001
    assert resultado["bounding_box_estado"]["min_lat"] == -23.5
    assert resultado["bounding_box_estado"]["max_lat"] == -21.5
    assert resultado["bounding_box_estado"]["min_lon"] == -44.5
    assert resultado["bounding_box_estado"]["max_lon"] == -42.5
    assert resultado["zoom_estado"] >= 8
