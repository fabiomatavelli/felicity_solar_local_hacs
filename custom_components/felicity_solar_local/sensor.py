"""Sensor platform for Felicity Solar Local."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FelicityLocalConfigEntry
from .const import DOMAIN
from .coordinator import FelicityLocalCoordinator

RAW_DATA_DESCRIPTION = SensorEntityDescription(
    key="raw_data",
    translation_key="raw_data",
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FelicityLocalConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Felicity Solar Local sensors for a config entry."""
    coordinator = entry.runtime_data

    entities: list[SensorEntity] = [
        FelicitySensor(coordinator, description)
        for description in coordinator.data.profile.sensors
    ]
    entities.append(FelicityRawDataSensor(coordinator))

    async_add_entities(entities)


class FelicityBaseSensor(CoordinatorEntity[FelicityLocalCoordinator], SensorEntity):
    """Shared device info for all sensors of one battery."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FelicityLocalCoordinator) -> None:
        super().__init__(coordinator)
        device_id = coordinator.data.data.get("serial_number") or (
            f"{coordinator.host}:{coordinator.port}"
        )
        self._device_id = device_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"Felicity Solar Battery {device_id}",
            manufacturer="Felicity Solar",
            model=coordinator.data.profile.name,
        )


class FelicitySensor(FelicityBaseSensor):
    """A single mapped sensor value from the battery's profile."""

    def __init__(
        self,
        coordinator: FelicityLocalCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._device_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.coordinator.data.data.get(self.entity_description.key)


class FelicityRawDataSensor(FelicityBaseSensor):
    """Diagnostic sensor exposing the full raw device payload as attributes.

    Ensures no field is ever silently lost, even for fields the active profile doesn't
    map to a dedicated sensor, and regardless of whether the profile is "verified" or
    "best_effort" for this particular battery model.
    """

    entity_description = RAW_DATA_DESCRIPTION

    def __init__(self, coordinator: FelicityLocalCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._device_id}_raw_data"

    @property
    def native_value(self) -> str:
        return datetime.now(UTC).isoformat()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "profile": self.coordinator.data.profile.name,
            "profile_confidence": self.coordinator.data.profile.confidence,
            "raw": self.coordinator.data.raw,
        }
