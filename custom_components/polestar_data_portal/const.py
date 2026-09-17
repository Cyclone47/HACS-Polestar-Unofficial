"""Constants for the Polestar Data Portal integration."""
from __future__ import annotations

try:
    from homeassistant.const import Platform

    PLATFORMS: list[Platform] = [
        Platform.SENSOR,
        Platform.BINARY_SENSOR,
        Platform.DEVICE_TRACKER,
        Platform.BUTTON,
    ]
except ImportError:
    PLATFORMS = ["sensor", "binary_sensor", "device_tracker", "button"]  # type: ignore[assignment]

DOMAIN = "polestar_data_portal"

# Configuration keys
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_ACCOUNT_ID = "account_id"
CONF_VIN = "vin"
CONF_SCAN_INTERVAL = "scan_interval"

# Default configuration values
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes (within 10,000 requests/day quota)
MIN_SCAN_INTERVAL = 60
MAX_SCAN_INTERVAL = 3600
DEFAULT_NAME = "Polestar"

# Polestar EU Data Act M2M API Endpoints
TOKEN_URL = "https://pc-api.polestar.com/eu-north-1/data-portal/m2m/token"
BASE_URL = "https://pc-api.polestar.com/eu-north-1/data-portal/m2m"
VEHICLES_URL = f"{BASE_URL}/v1/vehicles"

# Telemetry domains to fetch
TELEMETRY_ENDPOINTS: dict[str, str] = {
    "battery": "telemetry/battery",
    "odometer": "telemetry/odometer",
    "exterior": "telemetry/exterior",
    "location": "telemetry/location",
    "health": "telemetry/health",
    "availability": "telemetry/availability",
    "parking_climatization": "telemetry/parking-climatization",
    "pre_cleaning": "telemetry/pre-cleaning",
}

# Charging domains to fetch
CHARGING_ENDPOINTS: dict[str, str] = {
    "target_soc": "charging/target-soc",
    "amp_limit": "charging/amp-limit",
    "charge_locations": "charging/charge-locations",
    "charge_now": "charging/charge-now",
    "global_charge_timer": "charging/global-charge-timer",
    "parking_climate_timer": "charging/parking-climate-timer",
    "is_at_charge_location": "charging/is-at-charge-location",
}
