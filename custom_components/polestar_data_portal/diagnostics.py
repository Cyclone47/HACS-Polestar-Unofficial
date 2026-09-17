"""Diagnostics support for Polestar Data Portal."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_ACCOUNT_ID, CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_VIN, DOMAIN
from .coordinator import PolestarDataUpdateCoordinator

TO_REDACT = {
    CONF_CLIENT_SECRET,
    CONF_CLIENT_ID,
    CONF_ACCOUNT_ID,
    CONF_VIN,
    "accessToken",
    "access_token",
    "id",
    "metaEventId",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: PolestarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "entry_options": dict(entry.options),
        "coordinator_data": coordinator.data,
        "total_updates": coordinator.total_updates,
    }
