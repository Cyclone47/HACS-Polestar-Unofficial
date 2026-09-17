"""Binary sensor platform for Polestar Data Portal."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PolestarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class PolestarBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Polestar binary sensor entity."""

    is_on_fn: Callable[[dict[str, Any]], bool | None]


def _is_open(status: str | None) -> bool | None:
    """Check if door/window status is OPEN."""
    if status is None:
        return None
    return status in ("OPEN_STATUS_OPEN", "OPEN")


def _is_unlocked(status: str | None) -> bool | None:
    """Check if lock is UNLOCKED (HA BinarySensor lock class: ON = Unlocked)."""
    if status is None:
        return None
    return status not in ("LOCK_STATUS_LOCKED", "LOCKED")


def _has_light_warning(health_data: dict[str, Any] | None) -> bool | None:
    """Check if any exterior light has an active warning."""
    if not health_data or "lightWarnings" not in health_data:
        return None
    light_warnings = health_data.get("lightWarnings") or {}
    for _, warning in light_warnings.items():
        if warning and warning != "EXTERIOR_LIGHT_WARNING_NO_WARNING":
            return True
    return False


def _has_tyre_warning(health_data: dict[str, Any] | None) -> bool | None:
    """Check if any tyre has an active pressure warning."""
    if not health_data:
        return None
    tyres = [
        "frontLeftTyrePressureWarning",
        "frontRightTyrePressureWarning",
        "rearLeftTyrePressureWarning",
        "rearRightTyrePressureWarning",
    ]
    for tyre in tyres:
        warning = health_data.get(tyre)
        if warning and warning != "TYRE_PRESSURE_WARNING_NO_WARNING":
            return True
    return False


BINARY_SENSOR_DESCRIPTIONS: tuple[PolestarBinarySensorEntityDescription, ...] = (
    # Charging Binary Sensors
    PolestarBinarySensorEntityDescription(
        key="charger_connected",
        translation_key="charger_connected",
        device_class=BinarySensorDeviceClass.PLUG,
        is_on_fn=lambda data: (
            (data.get("battery") or {}).get("chargerConnectionStatus")
            == "CHARGER_CONNECTION_STATUS_CONNECTED"
        ),
    ),
    PolestarBinarySensorEntityDescription(
        key="battery_charging",
        translation_key="battery_charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        is_on_fn=lambda data: (
            (data.get("battery") or {}).get("chargingStatusV2")
            in (
                "CHARGING_STATUS_V2_CHARGING",
                "CHARGING_STATUS_CHARGING",
                "CHARGING_STATUS_V2_FAST_CHARGING",
            )
        ),
    ),
    PolestarBinarySensorEntityDescription(
        key="charge_now_active",
        translation_key="charge_now_active",
        device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:flash",
        is_on_fn=lambda data: (
            (data.get("charge_now") or {})
            .get("syncedOverrideChargeTimer", {})
            .get("override", False)
        ),
    ),
    PolestarBinarySensorEntityDescription(
        key="global_charge_timer_active",
        translation_key="global_charge_timer_active",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:timer-check",
        is_on_fn=lambda data: (
            (data.get("global_charge_timer") or {})
            .get("globalChargeTimer", {})
            .get("activated", False)
        ),
    ),
    # Doors
    PolestarBinarySensorEntityDescription(
        key="front_left_door",
        translation_key="front_left_door",
        device_class=BinarySensorDeviceClass.DOOR,
        is_on_fn=lambda data: _is_open((data.get("exterior") or {}).get("frontLeftDoor")),
    ),
    PolestarBinarySensorEntityDescription(
        key="front_right_door",
        translation_key="front_right_door",
        device_class=BinarySensorDeviceClass.DOOR,
        is_on_fn=lambda data: _is_open((data.get("exterior") or {}).get("frontRightDoor")),
    ),
    PolestarBinarySensorEntityDescription(
        key="rear_left_door",
        translation_key="rear_left_door",
        device_class=BinarySensorDeviceClass.DOOR,
        is_on_fn=lambda data: _is_open((data.get("exterior") or {}).get("rearLeftDoor")),
    ),
    PolestarBinarySensorEntityDescription(
        key="rear_right_door",
        translation_key="rear_right_door",
        device_class=BinarySensorDeviceClass.DOOR,
        is_on_fn=lambda data: _is_open((data.get("exterior") or {}).get("rearRightDoor")),
    ),
    # Windows
    PolestarBinarySensorEntityDescription(
        key="front_left_window",
        translation_key="front_left_window",
        device_class=BinarySensorDeviceClass.WINDOW,
        is_on_fn=lambda data: _is_open((data.get("exterior") or {}).get("frontLeftWindow")),
    ),
    PolestarBinarySensorEntityDescription(
        key="front_right_window",
        translation_key="front_right_window",
        device_class=BinarySensorDeviceClass.WINDOW,
        is_on_fn=lambda data: _is_open((data.get("exterior") or {}).get("frontRightWindow")),
    ),
    PolestarBinarySensorEntityDescription(
        key="rear_left_window",
        translation_key="rear_left_window",
        device_class=BinarySensorDeviceClass.WINDOW,
        is_on_fn=lambda data: _is_open((data.get("exterior") or {}).get("rearLeftWindow")),
    ),
    PolestarBinarySensorEntityDescription(
        key="rear_right_window",
        translation_key="rear_right_window",
        device_class=BinarySensorDeviceClass.WINDOW,
        is_on_fn=lambda data: _is_open((data.get("exterior") or {}).get("rearRightWindow")),
    ),
    # Hood, Tailgate & Flap
    PolestarBinarySensorEntityDescription(
        key="hood",
        translation_key="hood",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-hood",
        is_on_fn=lambda data: _is_open((data.get("exterior") or {}).get("hood")),
    ),
    PolestarBinarySensorEntityDescription(
        key="tailgate",
        translation_key="tailgate",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-back",
        is_on_fn=lambda data: _is_open((data.get("exterior") or {}).get("tailgate")),
    ),
    PolestarBinarySensorEntityDescription(
        key="tank_lid",
        translation_key="tank_lid",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:ev-plug-type2",
        is_on_fn=lambda data: _is_open((data.get("exterior") or {}).get("tankLid")),
    ),
    # Security & Locks
    PolestarBinarySensorEntityDescription(
        key="central_lock",
        translation_key="central_lock",
        device_class=BinarySensorDeviceClass.LOCK,
        is_on_fn=lambda data: _is_unlocked((data.get("exterior") or {}).get("centralLock")),
    ),
    PolestarBinarySensorEntityDescription(
        key="tailgate_lock",
        translation_key="tailgate_lock",
        device_class=BinarySensorDeviceClass.LOCK,
        is_on_fn=lambda data: _is_unlocked((data.get("exterior") or {}).get("tailgateLock")),
    ),
    PolestarBinarySensorEntityDescription(
        key="alarm",
        translation_key="alarm",
        device_class=BinarySensorDeviceClass.SAFETY,
        icon="mdi:shield-alert",
        is_on_fn=lambda data: (
            ((data.get("exterior") or {}).get("alarm") not in ("ALARM_STATUS_IDLE", "IDLE"))
            if (data.get("exterior") or {}).get("alarm") is not None
            else None
        ),
    ),
    # Climate & Pre-cleaning
    PolestarBinarySensorEntityDescription(
        key="parking_climate_running",
        translation_key="parking_climate_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:air-conditioner",
        is_on_fn=lambda data: (
            (data.get("parking_climatization") or {}).get("runningStatus") == "RUNNING_STATUS_ON"
        ),
    ),
    PolestarBinarySensorEntityDescription(
        key="pre_cleaning_running",
        translation_key="pre_cleaning_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:air-filter",
        is_on_fn=lambda data: (
            (data.get("pre_cleaning") or {}).get("runningStatus") == "RUNNING_STATUS_ON"
        ),
    ),
    PolestarBinarySensorEntityDescription(
        key="vehicle_available",
        translation_key="vehicle_available",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda data: (
            (data.get("availability") or {}).get("availabilityStatus")
            == "AVAILABILITY_STATUS_AVAILABLE"
        ),
    ),
    # Health Warnings (Problem class)
    PolestarBinarySensorEntityDescription(
        key="service_warning",
        translation_key="service_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:wrench-alert",
        is_on_fn=lambda data: (
            ((data.get("health") or {}).get("serviceWarning") not in ("SERVICE_WARNING_NO_WARNING", "NO_WARNING"))
            if (data.get("health") or {}).get("serviceWarning") is not None
            else None
        ),
    ),
    PolestarBinarySensorEntityDescription(
        key="brake_fluid_warning",
        translation_key="brake_fluid_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:car-brake-alert",
        is_on_fn=lambda data: (
            ((data.get("health") or {}).get("brakeFluidLevelWarning") not in ("BRAKE_FLUID_LEVEL_WARNING_NO_WARNING", "NO_WARNING"))
            if (data.get("health") or {}).get("brakeFluidLevelWarning") is not None
            else None
        ),
    ),
    PolestarBinarySensorEntityDescription(
        key="engine_coolant_warning",
        translation_key="engine_coolant_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:coolant-temperature",
        is_on_fn=lambda data: (
            ((data.get("health") or {}).get("engineCoolantLevelWarning") not in ("ENGINE_COOLANT_LEVEL_WARNING_NO_WARNING", "NO_WARNING"))
            if (data.get("health") or {}).get("engineCoolantLevelWarning") is not None
            else None
        ),
    ),
    PolestarBinarySensorEntityDescription(
        key="oil_level_warning",
        translation_key="oil_level_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:oil",
        is_on_fn=lambda data: (
            ((data.get("health") or {}).get("oilLevelWarning") not in ("OIL_LEVEL_WARNING_NO_WARNING", "NO_WARNING"))
            if (data.get("health") or {}).get("oilLevelWarning") is not None
            else None
        ),
    ),
    PolestarBinarySensorEntityDescription(
        key="washer_fluid_warning",
        translation_key="washer_fluid_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:wiper-wash",
        is_on_fn=lambda data: (
            ((data.get("health") or {}).get("washerFluidLevelWarning") not in ("WASHER_FLUID_LEVEL_WARNING_NO_WARNING", "NO_WARNING"))
            if (data.get("health") or {}).get("washerFluidLevelWarning") is not None
            else None
        ),
    ),
    PolestarBinarySensorEntityDescription(
        key="low_voltage_battery_warning",
        translation_key="low_voltage_battery_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:car-battery",
        is_on_fn=lambda data: (
            ((data.get("health") or {}).get("lowVoltageBatteryWarning") not in ("LOW_VOLTAGE_BATTERY_WARNING_NO_WARNING", "NO_WARNING"))
            if (data.get("health") or {}).get("lowVoltageBatteryWarning") is not None
            else None
        ),
    ),
    PolestarBinarySensorEntityDescription(
        key="tyre_pressure_warning",
        translation_key="tyre_pressure_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:car-tire-alert",
        is_on_fn=lambda data: _has_tyre_warning(data.get("health")),
    ),
    PolestarBinarySensorEntityDescription(
        key="exterior_light_warning",
        translation_key="exterior_light_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:car-light-alert",
        is_on_fn=lambda data: _has_light_warning(data.get("health")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Polestar binary sensor entities based on a config entry."""
    coordinator: PolestarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PolestarBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class PolestarBinarySensor(CoordinatorEntity[PolestarDataUpdateCoordinator], BinarySensorEntity):
    """Representation of a Polestar binary sensor."""

    entity_description: PolestarBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PolestarDataUpdateCoordinator,
        description: PolestarBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.vin = coordinator.vin
        self._attr_unique_id = f"{coordinator.vin}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.vin)},
            name=f"{coordinator.vin_info.get('model', 'Polestar')} ({coordinator.vin})",
            manufacturer="Polestar",
            model=coordinator.vin_info.get("model_display", "Polestar 2"),
            serial_number=coordinator.vin,
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.entity_description.is_on_fn(self.coordinator.data)
