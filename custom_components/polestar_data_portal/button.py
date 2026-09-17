"""Button platform for Polestar Data Portal."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
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
    """Set up Polestar button entities based on a config entry."""
    coordinator: PolestarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PolestarRefreshButton(coordinator)])


class PolestarRefreshButton(CoordinatorEntity[PolestarDataUpdateCoordinator], ButtonEntity):
    """Button to trigger an immediate data refresh from the Polestar API."""

    entity_description = ButtonEntityDescription(
        key="refresh_data",
        translation_key="refresh_data",
        icon="mdi:refresh",
    )
    _attr_has_entity_name = True

    def __init__(self, coordinator: PolestarDataUpdateCoordinator) -> None:
        """Initialize the refresh button."""
        super().__init__(coordinator)
        self.vin = coordinator.vin
        self._attr_unique_id = f"{coordinator.vin}_refresh_data"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.vin)},
            name=f"Polestar ({coordinator.vin})",
            manufacturer="Polestar",
            model="Polestar 2",
            serial_number=coordinator.vin,
        )

    async def async_press(self) -> None:
        """Press the button to request a data refresh."""
        _LOGGER.debug("Polestar refresh button pressed for VIN %s", self.vin)
        await self.coordinator.async_request_refresh()
