"""Constants for the Polestar Data Portal integration."""
from __future__ import annotations

try:
    from homeassistant.const import Platform

    PLATFORMS: list[Platform] = [
        Platform.SENSOR,
        Platform.BINARY_SENSOR,
        Platform.DEVICE_TRACKER,
        Platform.BUTTON,
        Platform.IMAGE,
    ]
except ImportError:
    PLATFORMS = ["sensor", "binary_sensor", "device_tracker", "button", "image"]  # type: ignore[assignment]

DOMAIN = "polestar_data_portal"

# Configuration keys
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_ACCOUNT_ID = "account_id"
CONF_VIN = "vin"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_CAR_COLOR = "car_color"

# Default configuration values
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes (within 10,000 requests/day quota)
MIN_SCAN_INTERVAL = 60
MAX_SCAN_INTERVAL = 3600
DEFAULT_NAME = "Polestar"
DEFAULT_CAR_COLOR = "midnight"

# Official 4K Transparent Polestar 2 Studio Renders from Polestar CMS
POLESTAR_COLORS: dict[str, dict[str, str]] = {
    "midnight": {
        "name": "Midnight",
        "hex": "#1b2a3a",
        "image": "https://www.polestar.com/dato-assets/94392/1773909417-10-3-polestar-2-27-overview-config-midnight-d.png",
    },
    "magnesium": {
        "name": "Magnesium",
        "hex": "#d4d8db",
        "image": "https://www.polestar.com/dato-assets/94392/1773909399-10-2-polestar-2-27-overview-config-vapour-d.png",
    },
    "snow": {
        "name": "Snow",
        "hex": "#f5f6f7",
        "image": "https://www.polestar.com/dato-assets/94392/1773909330-10-1-polestar-2-27-overview-config-snow-d.png",
    },
    "thunder": {
        "name": "Thunder",
        "hex": "#434a52",
        "image": "https://www.polestar.com/dato-assets/94392/1773909434-10-4-polestar-2-27-overview-config-storm-d.png",
    },
    "space": {
        "name": "Space / Void",
        "hex": "#111315",
        "image": "https://www.polestar.com/dato-assets/94392/1773909450-10-5-polestar-2-27-overview-config-space-d.png",
    },
    "jupiter": {
        "name": "Jupiter",
        "hex": "#b3a595",
        "image": "https://www.polestar.com/dato-assets/94392/1774276445-10-6-polestar-2-27-overview-config-dune-d.png",
    },
}

# Official transparent renders for other Polestar vehicles
POLESTAR_MODEL_IMAGES: dict[str, str] = {
    "Polestar 2": "https://www.polestar.com/dato-assets/11286/1743511706-megamenu-p2.png",
    "Polestar 3": "https://www.polestar.com/dato-assets/11286/1759244063-megamenu-ps3-my26.png",
    "Polestar 4": "https://www.polestar.com/dato-assets/11286/1776262345-megamenu-ps4-my27.png",
    "Polestar 5": "https://www.polestar.com/dato-assets/11286/1764240549-megamenu-ps5.png",
}

# Standard ISO 3779 model year codes for Polestar
VIN_MODEL_YEARS: dict[str, int] = {
    "L": 2020,
    "M": 2021,
    "N": 2022,
    "P": 2023,
    "R": 2024,
    "S": 2025,
    "T": 2026,
    "V": 2027,
}

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
