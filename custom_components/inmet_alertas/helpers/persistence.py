"""Merge e expiração de alertas persistentes (lógica pura, sem HA).

Para manter a testabilidade em `tests/unit`, este módulo usa apenas a
biblioteca padrão (`datetime`), sem depender de `homeassistant.util.dt`.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


def _parse_iso(valor: str, referencia: datetime) -> datetime | None:
    """Converte uma string ISO em datetime; None quando não for parseável."""
    texto = valor.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(texto)
    except ValueError:
        return None
    if parsed.tzinfo is None and referencia.tzinfo is not None:
        parsed = parsed.replace(tzinfo=referencia.tzinfo)
    return parsed


def alerta_ainda_valido(alert_data: dict[str, Any], agora: datetime) -> bool:
    """True se o alerta não expirou.

    Considera apenas campos em formato ISO (contêm "T"); datas já formatadas
    em pt-BR são ignoradas. Sem data avaliável, assume válido para não perder
    alertas por falha de parsing.
    """
    for campo in ("expires", "fim"):
        valor = alert_data.get(campo) or ""
        if "T" not in valor:
            continue
        fim = _parse_iso(valor, agora)
        if fim is not None:
            return fim > agora
    return True


def mesclar_alertas(
    persistentes: dict[str, dict[str, Any]],
    novos_alertas: list[dict[str, Any]],
    agora: datetime,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Mantém alertas válidos, funde os novos dados e devolve o novo cache.

    Alertas expirados saem; alertas do scan atual atualizam os existentes
    (merge raso, sem mutar os dicionários originais).
    """
    finais: dict[str, dict[str, Any]] = {}

    for alert_id, alert_data in persistentes.items():
        if alerta_ainda_valido(alert_data, agora):
            finais[alert_id] = alert_data

    for novo in novos_alertas:
        alert_id = novo["id"]
        if alert_id in finais:
            finais[alert_id] = {**finais[alert_id], **novo}
        else:
            finais[alert_id] = novo

    return list(finais.values()), finais
