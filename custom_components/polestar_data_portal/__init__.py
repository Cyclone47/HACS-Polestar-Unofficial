"""The Polestar Data Portal integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PolestarApiClient
from .const import (
    CONF_ACCOUNT_ID,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_SCAN_INTERVAL,
    CONF_VIN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import PolestarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Polestar Data Portal from a config entry."""
    client_id = entry.data[CONF_CLIENT_ID]
    client_secret = entry.data[CONF_CLIENT_SECRET]
    account_id = entry.data[CONF_ACCOUNT_ID]
    vin = entry.data[CONF_VIN]

    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    session = async_get_clientsession(hass)
    api = PolestarApiClient(
        client_id=client_id,
        client_secret=client_secret,
        account_id=account_id,
        session=session,
    )

    coordinator = PolestarDataUpdateCoordinator(
        hass=hass,
        api=api,
        vin=vin,
        update_interval=scan_interval,
    )

    # Perform first data refresh
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Register options update listener
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Set up entity platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Polestar Data Portal config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options updates."""
    if coordinator := hass.data.get(DOMAIN, {}).get(entry.entry_id):
        new_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        _LOGGER.debug("Updating Polestar polling interval to %d seconds", new_interval)
        coordinator.update_interval = timedelta(seconds=new_interval)
        await coordinator.async_refresh()
