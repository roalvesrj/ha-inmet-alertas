"""Montagem de atributos dos sensores a partir dos alertas processados.

Lógica pura (sem dependências do Home Assistant) para manter o código
testável em `tests/unit`.
"""
from __future__ import annotations

from typing import Any

from ..const import CORES_INMET_MAPA, MAX_MUNICIPIOS_EXIBIDOS, SEVERIDADE_PRIORIDADES


def preparar_alertas_para_atributos(
    alertas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Copia os alertas removendo a geometria (exposta pelo sensor de mapa)."""
    resultado = []
    for alerta in alertas:
        copia = dict(alerta)
        copia.pop("dados_geograficos", None)
        resultado.append(copia)
    return resultado


def calcular_resumo(alertas: list[dict[str, Any]]) -> dict[str, Any]:
    """Resumo dos alertas: contagem por severidade, máxima e municípios únicos."""
    severidades: dict[str, int] = {}
    municipios: set[str] = set()
    severidade_maxima = None
    max_prioridade = 0

    for alerta in alertas:
        severidade = alerta.get("severidade", "Desconhecida")
        severidades[severidade] = severidades.get(severidade, 0) + 1

        prioridade = SEVERIDADE_PRIORIDADES.get(severidade, 0)
        if prioridade > max_prioridade:
            max_prioridade = prioridade
            severidade_maxima = severidade

        municipios.update(alerta.get("municipios_estado", []))

    return {
        "alertas_por_severidade": severidades,
        "severidade_maxima": severidade_maxima,
        "municipios_unicos": len(municipios),
        "municipios_afetados": sorted(municipios)[:MAX_MUNICIPIOS_EXIBIDOS],
    }


def _zoom_por_bbox(bbox: dict[str, float]) -> int:
    """Zoom recomendado a partir da extensão da bounding box combinada."""
    extensao_lat = bbox["max_lat"] - bbox["min_lat"]
    extensao_lon = bbox["max_lon"] - bbox["min_lon"]
    extensao_max = max(extensao_lat, extensao_lon)

    if extensao_max > 5:
        return 6
    if extensao_max > 2:
        return 7
    if extensao_max > 1:
        return 8
    if extensao_max > 0.5:
        return 9
    return 10


def _poligono_para_info(
    alerta: dict[str, Any], poligono: dict[str, Any], indice: int
) -> dict[str, Any]:
    """Monta os dados de um polígono para consumo do plugin de mapa."""
    return {
        "id": f"{alerta.get('id', 'desconhecido')}_{indice}",
        "alerta_id": alerta.get("id"),
        "evento": alerta.get("evento", ""),
        "severidade": alerta.get("severidade", "Perigo Potencial"),
        "cor": alerta.get("color_risk", "#808080"),
        "coordenadas": poligono.get("coordenadas", []),
        "area_km2": poligono.get("area_km2", 0),
        "centro": poligono.get("centro"),
        "bounding_box": poligono.get("bounding_box"),
        "inicio": alerta.get("onset", ""),
        "fim": alerta.get("expires", ""),
        "descricao": str(alerta.get("descricao", ""))[:100],
        "municipios": alerta.get("municipios_estado", [])[:5],
    }


def construir_atributos_mapa(
    estado: str,
    alertas: list[dict[str, Any]],
    ultima_atualizacao: str | None,
) -> dict[str, Any]:
    """Atributos completos do sensor de mapa (polígonos, áreas, centro, zoom)."""
    poligonos_por_severidade: dict[str, list[dict[str, Any]]] = {}
    area_total = 0.0
    centros: list[list[float]] = []
    bboxes: list[dict[str, float]] = []
    total_alertas_com_geo = 0

    for alerta in alertas:
        dados_geo = alerta.get("dados_geograficos")
        if not dados_geo:
            continue

        total_alertas_com_geo += 1
        severidade = alerta.get("severidade", "Perigo Potencial")
        area_total += dados_geo.get("area_total_km2", 0)

        centro = dados_geo.get("centro_geografico")
        if centro:
            centros.append(centro)
        bbox = dados_geo.get("bounding_box")
        if bbox:
            bboxes.append(bbox)

        for indice, poligono in enumerate(dados_geo.get("poligonos_individuais", [])):
            poligonos_por_severidade.setdefault(severidade, []).append(
                _poligono_para_info(alerta, poligono, indice)
            )

    severidades_ordenadas = sorted(
        poligonos_por_severidade,
        key=lambda sev: SEVERIDADE_PRIORIDADES.get(sev, 0),
        reverse=True,
    )

    todos_poligonos = [
        poligono
        for severidade in severidades_ordenadas
        for poligono in poligonos_por_severidade[severidade]
    ]

    centro_combinado = None
    if centros:
        centro_combinado = [
            sum(c[0] for c in centros) / len(centros),
            sum(c[1] for c in centros) / len(centros),
        ]

    bbox_combinado = None
    zoom_recomendado = 8
    if bboxes:
        bbox_combinado = {
            "min_lat": min(b["min_lat"] for b in bboxes),
            "max_lat": max(b["max_lat"] for b in bboxes),
            "min_lon": min(b["min_lon"] for b in bboxes),
            "max_lon": max(b["max_lon"] for b in bboxes),
        }
        zoom_recomendado = _zoom_por_bbox(bbox_combinado)

    camadas_sobrepostas = {
        severidade: {
            "cor": CORES_INMET_MAPA.get(severidade, "#808080"),
            "total_poligonos": len(poligonos_por_severidade[severidade]),
            "area_total_km2": sum(
                p["area_km2"] for p in poligonos_por_severidade[severidade]
            ),
            "poligonos": poligonos_por_severidade[severidade],
        }
        for severidade in severidades_ordenadas
    }

    return {
        "estado": estado,
        "poligonos": todos_poligonos,
        "area_total_afetada_km2": round(area_total, 2),
        "centro_geografico": centro_combinado,
        "bounding_box": bbox_combinado,
        "zoom_recomendado": zoom_recomendado,
        "camadas_por_severidade": camadas_sobrepostas,
        "total_alertas_com_geo": total_alertas_com_geo,
        "ultima_atualizacao": ultima_atualizacao,
    }
