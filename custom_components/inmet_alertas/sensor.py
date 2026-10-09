"""Sensores da integração INMET Alertas (entidades finas sobre o coordenador)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import InmetAlertasConfigEntry, INMETDataUpdateCoordinator
from .entity import INMETBaseSensor
from .helpers.sensor_data import (
    calcular_resumo,
    construir_atributos_mapa,
    preparar_alertas_para_atributos,
)

# Atualizações centralizadas no coordenador (regra parallel-updates do Silver)
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: InmetAlertasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurar os sensores dos alertas INMET."""
    coordinator = config_entry.runtime_data
    async_add_entities(
        [
            INMETAlertasSensor(coordinator),
            INMETAlertasCountSensor(coordinator),
            INMETAlertasMapaSensor(coordinator),
            INMETAlertasDiagnosticoSensor(coordinator),
        ]
    )


class INMETAlertasSensor(INMETBaseSensor, SensorEntity):
    """Sensor principal dos alertas INMET."""

    _attr_icon = "mdi:weather-cloudy-alert"

    def __init__(self, coordinator: INMETDataUpdateCoordinator) -> None:
        """Inicializar sensor principal."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{self._estado}_alertas"
        self._attr_name = f"Alertas Meteorológicos {self._estado}"

    @property
    def native_value(self) -> str | None:
        """Nome do alerta ativo ou resumo da quantidade (None sem dados)."""
        if not self.coordinator.data:
            return None

        alerts = self.coordinator.data.get("alerts") or []
        if not alerts:
            return "Nenhum alerta ativo"
        if len(alerts) == 1:
            return alerts[0]["titulo"]
        return f"{len(alerts)} alertas ativos"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Atributos com a lista de alertas (sem geometria) e o resumo."""
        data = self.coordinator.data
        if not data:
            return {
                "estado": self._estado,
                "total_alertas": 0,
                "ultima_atualizacao": None,
                "alertas": [],
                "alertas_por_severidade": {},
                "severidade_maxima": None,
                "municipios_unicos": 0,
                "municipios_afetados": [],
            }

        alerts = data.get("alerts") or []
        attributes: dict[str, Any] = {
            "estado": self._estado,
            "total_alertas": data.get("count", 0),
            "ultima_atualizacao": data.get("last_update"),
            "alertas": preparar_alertas_para_atributos(alerts),
        }
        attributes.update(calcular_resumo(alerts))
        return attributes


class INMETAlertasCountSensor(INMETBaseSensor, SensorEntity):
    """Sensor de contagem de alertas INMET."""

    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = "alertas"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: INMETDataUpdateCoordinator) -> None:
        """Inicializar sensor de contagem."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{self._estado}_count"
        self._attr_name = f"Quantidade de Alertas {self._estado}"

    @property
    def native_value(self) -> int | None:
        """Contagem de alertas ativos (None sem dados)."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Atributos básicos do sensor de contagem."""
        if not self.coordinator.data:
            return {"estado": self._estado, "ultima_atualizacao": None}

        return {
            "estado": self._estado,
            "ultima_atualizacao": self.coordinator.data.get("last_update"),
        }


class INMETAlertasMapaSensor(INMETBaseSensor, SensorEntity):
    """Sensor de mapa geográfico dos alertas INMET."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "polígonos"
    _attr_icon = "mdi:map-marker-multiple"

    def __init__(self, coordinator: INMETDataUpdateCoordinator) -> None:
        """Inicializar sensor de mapa."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_mapa_{self._estado}"
        self._attr_name = f"INMET Alertas Mapa {self._estado}"

    @property
    def native_value(self) -> int | None:
        """Número de polígonos com dados geográficos (None sem dados)."""
        if not self.coordinator.data:
            return None

        total = 0
        for alerta in self.coordinator.data.get("alerts") or []:
            dados_geo = alerta.get("dados_geograficos")
            if dados_geo and dados_geo.get("poligonos_individuais"):
                total += len(dados_geo["poligonos_individuais"])
        return total

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Atributos de mapa (polígonos, áreas, centro, zoom)."""
        data = self.coordinator.data or {}
        return construir_atributos_mapa(
            self._estado,
            data.get("alerts") or [],
            data.get("last_update"),
        )


class INMETAlertasDiagnosticoSensor(INMETBaseSensor, SensorEntity):
    """Sensor de diagnóstico dos alertas INMET."""

    _attr_icon = "mdi:information-outline"

    def __init__(self, coordinator: INMETDataUpdateCoordinator) -> None:
        """Inicializar sensor de diagnóstico."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{self._estado}_diagnostico"
        self._attr_name = f"Diagnóstico INMET {self._estado}"

    @property
    def native_value(self) -> str | None:
        """Status do último ciclo (erro/rate_limit/ok/desconhecido)."""
        if not self.coordinator.data:
            return None

        diagnostico = self.coordinator.data.get("diagnostico", {})
        if diagnostico.get("ultimo_ciclo_com_erro"):
            return "erro"
        if diagnostico.get("ultimo_ciclo_rate_limited"):
            return "rate_limit"
        if diagnostico.get("ultimo_http_status") == 200:
            return "ok"
        return "desconhecido"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Atributos do último ciclo de atualização."""
        attrs: dict[str, Any] = {"estado": self._estado}
        if self.coordinator.data:
            diagnostico = self.coordinator.data.get("diagnostico", {})
            attrs.update(
                {
                    "ultimo_http_status": diagnostico.get("ultimo_http_status"),
                    "rate_limit_hits": diagnostico.get("rate_limit_hits", 0),
                    "pending_caps": diagnostico.get("pending_caps", 0),
                    "ultimo_erro": diagnostico.get("ultimo_erro"),
                    "total_alertas_api": diagnostico.get("total_alertas_api", 0),
                    "ciclo_atual": diagnostico.get("ciclo_atual"),
                    "ultimo_ciclo_com_erro": diagnostico.get(
                        "ultimo_ciclo_com_erro", False
                    ),
                    "ultimo_ciclo_rate_limited": diagnostico.get(
                        "ultimo_ciclo_rate_limited", False
                    ),
                }
            )
        return attrs
