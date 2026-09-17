"""Device tracker platform for Polestar Data Portal."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PolestarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Polestar device tracker based on a config entry."""
    coordinator: PolestarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PolestarDeviceTracker(coordinator)])


class PolestarDeviceTracker(CoordinatorEntity[PolestarDataUpdateCoordinator], TrackerEntity):
    """Polestar vehicle GPS device tracker."""

    _attr_has_entity_name = True
    _attr_translation_key = "location"
    _attr_name = "Location"

    def __init__(self, coordinator: PolestarDataUpdateCoordinator) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self.vin = coordinator.vin
        self._attr_unique_id = f"{coordinator.vin}_location"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.vin)},
            name=f"Polestar ({coordinator.vin})",
            manufacturer="Polestar",
            model="Polestar 2",
            serial_number=coordinator.vin,
        )

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the device tracker."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        loc = (self.coordinator.data.get("location") or {}).get("coordinate") or {}
        lat = loc.get("latitude")
        return float(lat) if lat is not None else None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        loc = (self.coordinator.data.get("location") or {}).get("coordinate") or {}
        lon = loc.get("longitude")
        return float(lon) if lon is not None else None

    @property
    def battery_level(self) -> int | None:
        """Return the battery level of the device."""
        return (self.coordinator.data.get("battery") or {}).get("batteryChargeLevelPercentage")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra device tracker attributes."""
        loc = self.coordinator.data.get("location") or {}

        speed_raw = loc.get("speed")
        altitude_raw = loc.get("altitude")

        speed = None
        if speed_raw is not None:
            try:
                speed = float(speed_raw)
            except (ValueError, TypeError):
                speed = None

        altitude = None
        if altitude_raw is not None:
            try:
                altitude = float(altitude_raw)
            except (ValueError, TypeError):
                altitude = None

        return {
            "heading": loc.get("heading"),
            "altitude": altitude,
            "speed": speed,
            "meta_received_at": loc.get("metaReceivedAt"),
        }
