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
