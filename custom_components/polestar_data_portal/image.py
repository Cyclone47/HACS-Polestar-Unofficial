"""Support for Polestar vehicle image entity."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import homeassistant.util.dt as dt_util

from .const import DEFAULT_CAR_COLOR, DOMAIN, POLESTAR_COLORS
from .coordinator import PolestarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Polestar image entity from a config entry."""
    coordinator: PolestarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PolestarVehicleImage(coordinator, hass)], True)


class PolestarVehicleImage(CoordinatorEntity[PolestarDataUpdateCoordinator], ImageEntity):
    """Representation of an official transparent Polestar vehicle studio render."""

    _attr_has_entity_name = True
    _attr_translation_key = "vehicle_image"

    def __init__(
        self,
        coordinator: PolestarDataUpdateCoordinator,
        hass: HomeAssistant,
    ) -> None:
        """Initialize the Polestar vehicle image."""
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)

        self._attr_unique_id = f"{coordinator.vin}_vehicle_image"
        self._cached_image_url: str | None = None
        self._cached_image_bytes: bytes | None = None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.vin)},
            name=f"{coordinator.vin_info.get('model', 'Polestar')} ({coordinator.vin})",
            manufacturer="Polestar",
            model=coordinator.vin_info.get("model_display", "Polestar 2"),
            serial_number=coordinator.vin,
        )

    @property
    def image_url(self) -> str | None:
        """Return the URL of the official vehicle render."""
        return self.coordinator.get_vehicle_image_url()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes for the vehicle image."""
        color_info = POLESTAR_COLORS.get(
            self.coordinator.car_color,
            POLESTAR_COLORS.get(DEFAULT_CAR_COLOR, {}),
        )
        return {
            "car_color": self.coordinator.car_color,
            "car_color_name": color_info.get("name", self.coordinator.car_color.title()),
            "car_color_hex": color_info.get("hex", "#1b2a3a"),
            "model": self.coordinator.vin_info.get("model", "Polestar 2"),
            "model_year": self.coordinator.vin_info.get("model_year"),
            "model_display": self.coordinator.vin_info.get("model_display", "Polestar 2"),
            "vin": self.coordinator.vin,
        }

    async def async_image(self) -> bytes | None:
        """Return bytes of the vehicle image with memory caching."""
        current_url = self.image_url
        if not current_url:
            return None

        # Return cached bytes if URL hasn't changed
        if self._cached_image_bytes is not None and self._cached_image_url == current_url:
            return self._cached_image_bytes

        try:
            session = self.coordinator.api._session
            async with session.get(current_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    self._cached_image_bytes = await resp.read()
                    self._cached_image_url = current_url
                    self._attr_image_last_updated = dt_util.utcnow()
                    _LOGGER.debug(
                        "Cached Polestar vehicle render for %s (%d bytes)",
                        self.coordinator.vin,
                        len(self._cached_image_bytes),
                    )
                    return self._cached_image_bytes
                _LOGGER.warning(
                    "Failed to fetch vehicle image from %s (HTTP %d)",
                    current_url,
                    resp.status,
                )
        except Exception as err:
            _LOGGER.warning("Error downloading vehicle image for %s: %s", self.coordinator.vin, err)

        return self._cached_image_bytes
