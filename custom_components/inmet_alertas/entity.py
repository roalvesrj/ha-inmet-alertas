"""Classe base das entidades da integração INMET Alertas."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import INMETDataUpdateCoordinator


class INMETBaseSensor(CoordinatorEntity[INMETDataUpdateCoordinator], SensorEntity):
    """Base comum dos sensores: nome de entidade, atribuição e estado configurado."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: INMETDataUpdateCoordinator) -> None:
        """Inicializar sensor a partir do coordenador."""
        super().__init__(coordinator)
        self._estado = coordinator.estado
