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
from .const import (
    DEFAULT_CAR_COLOR,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    POLESTAR_COLORS,
    POLESTAR_MODEL_IMAGES,
    VIN_MODEL_YEARS,
)

_LOGGER = logging.getLogger(__name__)


def decode_vin(vin: str) -> dict[str, Any]:
    """Decode standard ISO 3779 / Polestar VIN attributes."""
    model = "Polestar 2"
    if len(vin) >= 6:
        v_desc = vin[3:8].upper()
        if "ED" in v_desc or "3" in v_desc:
            model = "Polestar 3"
        elif "EF" in v_desc or "4" in v_desc:
            model = "Polestar 4"
        elif "5" in v_desc:
            model = "Polestar 5"
        elif "VS" in v_desc:
            model = "Polestar 2"

    year = None
    if len(vin) >= 10:
        year_char = vin[9].upper()
        year = VIN_MODEL_YEARS.get(year_char)

    model_display = f"{model} ({year})" if year else model
    return {
        "model": model,
        "model_year": year,
        "model_display": model_display,
        "manufacturer": "Polestar",
    }


class PolestarDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Polestar data from the official Data Portal API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: PolestarApiClient,
        vin: str,
        update_interval: int = DEFAULT_SCAN_INTERVAL,
        car_color: str = DEFAULT_CAR_COLOR,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.vin = vin
        self.car_color = car_color
        self.vin_info = decode_vin(vin)
        self.total_updates = 0

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{vin}",
            update_interval=timedelta(seconds=update_interval),
        )

    def get_vehicle_image_url(self) -> str:
        """Get official high-res studio render URL based on model and selected color."""
        model = self.vin_info.get("model", "Polestar 2")
        if model == "Polestar 2":
            color_data = POLESTAR_COLORS.get(self.car_color, POLESTAR_COLORS[DEFAULT_CAR_COLOR])
            return color_data["image"]
        return POLESTAR_MODEL_IMAGES.get(model, POLESTAR_MODEL_IMAGES["Polestar 2"])

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch vehicle telemetry and charging state from the API."""
        try:
            data = await self.api.async_get_all_telemetry(self.vin)
            self.total_updates += 1

            # Enrich with model and color attributes
            color_info = POLESTAR_COLORS.get(self.car_color, POLESTAR_COLORS.get(DEFAULT_CAR_COLOR, {}))
            data["car_color"] = self.car_color
            data["car_color_name"] = color_info.get("name", self.car_color.title())
            data["car_color_hex"] = color_info.get("hex", "#1b2a3a")
            data["car_image_url"] = self.get_vehicle_image_url()
            data["model"] = self.vin_info["model"]
            data["model_year"] = self.vin_info["model_year"]
            data["model_display"] = self.vin_info["model_display"]

            _LOGGER.debug(
                "Successfully polled Polestar Data Portal for VIN %s (%s, update #%d)",
                self.vin,
                self.vin_info["model_display"],
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
