"""DataUpdateCoordinator for Polestar Data Portal."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    PolestarApiClient,
    PolestarAuthError,
    PolestarConnectionError,
    PolestarRateLimitError,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PolestarDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Polestar data from the official Data Portal API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: PolestarApiClient,
        vin: str,
        update_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.vin = vin
        self.total_updates = 0

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{vin}",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch vehicle telemetry and charging state from the API."""
        try:
            data = await self.api.async_get_all_telemetry(self.vin)
            self.total_updates += 1
            _LOGGER.debug(
                "Successfully polled Polestar Data Portal for VIN %s (update #%d)",
                self.vin,
                self.total_updates,
            )
            return data
        except PolestarAuthError as err:
            _LOGGER.error("Authentication error polling Polestar for %s: %s", self.vin, err)
            raise ConfigEntryAuthFailed(err) from err
        except PolestarRateLimitError as err:
            _LOGGER.warning("Rate limit reached polling Polestar for %s: %s", self.vin, err)
            raise UpdateFailed(f"Polestar API rate limit reached: {err}") from err
        except PolestarConnectionError as err:
            _LOGGER.warning("Connection error polling Polestar for %s: %s", self.vin, err)
            raise UpdateFailed(f"Error communicating with Polestar API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error polling Polestar for %s: %s", self.vin, err)
            raise UpdateFailed(f"Unexpected error: {err}") from err
