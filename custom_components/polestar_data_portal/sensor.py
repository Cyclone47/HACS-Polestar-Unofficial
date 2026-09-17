"""Sensor platform for Polestar Data Portal."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfPower,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PolestarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class PolestarSensorEntityDescription(SensorEntityDescription):
    """Describes Polestar sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]


def _format_time_obj(time_obj: dict[str, Any] | None) -> str | None:
    """Format hour and minute object to HH:MM."""
    if not time_obj or "hour" not in time_obj:
        return None
    hour = time_obj.get("hour", 0)
    minute = time_obj.get("minute", 0)
    return f"{hour:02d}:{minute:02d}"


def _calculate_full_charge_range(data: dict[str, Any]) -> float | None:
    """Calculate theoretical full range at 100% SoC."""
    battery = data.get("battery") or {}
    soc = battery.get("batteryChargeLevelPercentage")
    range_km = battery.get("estimatedDistanceToEmptyKm")
    if soc and range_km and soc > 0:
        return round((range_km / soc) * 100, 1)
    return None


def _calculate_charging_end_time(data: dict[str, Any]) -> datetime | None:
    """Calculate estimated charging completion datetime."""
    battery = data.get("battery") or {}
    mins = battery.get("estimatedChargingTimeToFullMinutes")
    status = battery.get("chargingStatusV2")
    if mins and mins > 0 and status in ("CHARGING_STATUS_V2_CHARGING", "CHARGING_STATUS_CHARGING"):
        return datetime.now(timezone.utc) + timedelta(minutes=mins)
    return None


def _clean_enum_value(val: str | None, prefix: str) -> str | None:
    """Normalize raw API enum to lowercase for Home Assistant translation matching."""
    if not val:
        return None
    val_str = str(val).upper()
    if val_str.startswith(prefix):
        val_str = val_str[len(prefix):]
    return val_str.lower()


SENSOR_DESCRIPTIONS: tuple[PolestarSensorEntityDescription, ...] = (
    # Battery & Charging Sensors
    PolestarSensorEntityDescription(
        key="battery_level",
        translation_key="battery_level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("battery") or {}).get("batteryChargeLevelPercentage"),
    ),
    PolestarSensorEntityDescription(
        key="estimated_full_charge_range",
        translation_key="estimated_full_charge_range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-100",
        value_fn=_calculate_full_charge_range,
    ),
    PolestarSensorEntityDescription(
        key="estimated_charging_end_time",
        translation_key="estimated_charging_end_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-check-outline",
        value_fn=_calculate_charging_end_time,
    ),
    PolestarSensorEntityDescription(
        key="last_telemetry_update",
        translation_key="last_telemetry_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("meta_last_updated"),
    ),
    PolestarSensorEntityDescription(
        key="estimated_range",
        translation_key="estimated_range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
        value_fn=lambda data: (data.get("battery") or {}).get("estimatedDistanceToEmptyKm"),
    ),
    PolestarSensorEntityDescription(
        key="estimated_range_miles",
        translation_key="estimated_range_miles",
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
        entity_registry_enabled_default=False,
        value_fn=lambda data: (data.get("battery") or {}).get("estimatedDistanceToEmptyMiles"),
    ),
    PolestarSensorEntityDescription(
        key="average_energy_consumption",
        translation_key="average_energy_consumption",
        native_unit_of_measurement="kWh/100km",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge",
        value_fn=lambda data: (data.get("battery") or {}).get("averageEnergyConsumptionKwhPer100Km"),
    ),
    PolestarSensorEntityDescription(
        key="estimated_charging_time",
        translation_key="estimated_charging_time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        icon="mdi:timer-outline",
        value_fn=lambda data: (data.get("battery") or {}).get("estimatedChargingTimeToFullMinutes"),
    ),
    PolestarSensorEntityDescription(
        key="charging_power",
        translation_key="charging_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("battery") or {}).get("chargingPowerWatts"),
    ),
    PolestarSensorEntityDescription(
        key="charging_current",
        translation_key="charging_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("battery") or {}).get("chargingCurrentAmps"),
    ),
    PolestarSensorEntityDescription(
        key="charging_voltage",
        translation_key="charging_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("battery") or {}).get("chargingVoltageVolts"),
    ),
    PolestarSensorEntityDescription(
        key="charging_status",
        translation_key="charging_status",
        device_class=SensorDeviceClass.ENUM,
        options=["idle", "charging", "fast_charging", "done", "scheduled", "fault", "disconnected", "unspecified"],
        icon="mdi:ev-station",
        value_fn=lambda data: _clean_enum_value((data.get("battery") or {}).get("chargingStatusV2"), "CHARGING_STATUS_V2_"),
    ),
    PolestarSensorEntityDescription(
        key="charging_type",
        translation_key="charging_type",
        device_class=SensorDeviceClass.ENUM,
        options=["none", "ac", "dc", "unspecified"],
        icon="mdi:lightning-bolt",
        value_fn=lambda data: _clean_enum_value((data.get("battery") or {}).get("chargingType"), "CHARGING_TYPE_"),
    ),
    PolestarSensorEntityDescription(
        key="charger_power_status",
        translation_key="charger_power_status",
        device_class=SensorDeviceClass.ENUM,
        options=["no_power_available", "power_available", "charging"],
        icon="mdi:power",
        entity_registry_enabled_default=False,
        value_fn=lambda data: _clean_enum_value((data.get("battery") or {}).get("chargerPowerStatus"), "CHARGER_POWER_STATUS_"),
    ),
    # Charging Settings
    PolestarSensorEntityDescription(
        key="target_soc",
        translation_key="target_soc",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        icon="mdi:battery-charging-high",
        value_fn=lambda data: (
            (data.get("target_soc") or {}).get("targetSoc", {}).get("batteryChargeTargetLevel")
        ),
    ),
    PolestarSensorEntityDescription(
        key="amp_limit",
        translation_key="amp_limit",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        icon="mdi:current-ac",
        value_fn=lambda data: (
            (data.get("amp_limit") or {}).get("ampLimit", {}).get("ampLimit")
        ),
    ),
    # Odometer & Trips
    PolestarSensorEntityDescription(
        key="odometer",
        translation_key="odometer",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
        value_fn=lambda data: (
            round((data.get("odometer") or {}).get("odometerMeters", 0) / 1000.0, 1)
            if (data.get("odometer") or {}).get("odometerMeters") is not None
            else None
        ),
    ),
    PolestarSensorEntityDescription(
        key="trip_meter_manual",
        translation_key="trip_meter_manual",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:map-marker-distance",
        value_fn=lambda data: (
            round((data.get("odometer") or {}).get("tripMeterManualKm", 0), 1)
            if (data.get("odometer") or {}).get("tripMeterManualKm") is not None
            else None
        ),
    ),
    PolestarSensorEntityDescription(
        key="trip_meter_automatic",
        translation_key="trip_meter_automatic",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:map-marker-distance",
        value_fn=lambda data: (
            round((data.get("odometer") or {}).get("tripMeterAutomaticKm", 0), 1)
            if (data.get("odometer") or {}).get("tripMeterAutomaticKm") is not None
            else None
        ),
    ),
    PolestarSensorEntityDescription(
        key="average_speed_manual",
        translation_key="average_speed_manual",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        icon="mdi:speedometer",
        value_fn=lambda data: (data.get("odometer") or {}).get("averageSpeedKmPerHour"),
    ),
    PolestarSensorEntityDescription(
        key="average_speed_automatic",
        translation_key="average_speed_automatic",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        icon="mdi:speedometer",
        value_fn=lambda data: (data.get("odometer") or {}).get("averageSpeedKmPerHourAutomatic"),
    ),
    # Health & Service
    PolestarSensorEntityDescription(
        key="days_to_service",
        translation_key="days_to_service",
        native_unit_of_measurement=UnitOfTime.DAYS,
        device_class=SensorDeviceClass.DURATION,
        icon="mdi:wrench-clock",
        value_fn=lambda data: (data.get("health") or {}).get("daysToService"),
    ),
    PolestarSensorEntityDescription(
        key="distance_to_service",
        translation_key="distance_to_service",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        icon="mdi:wrench",
        value_fn=lambda data: (data.get("health") or {}).get("distanceToServiceKm"),
    ),
    PolestarSensorEntityDescription(
        key="engine_hours_to_service",
        translation_key="engine_hours_to_service",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        icon="mdi:clock-outline",
        entity_registry_enabled_default=False,
        value_fn=lambda data: (data.get("health") or {}).get("engineHoursToService"),
    ),
    # Tyre Pressures
    PolestarSensorEntityDescription(
        key="tyre_pressure_front_left",
        translation_key="tyre_pressure_front_left",
        native_unit_of_measurement=UnitOfPressure.KPA,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-tire-alert",
        value_fn=lambda data: (data.get("health") or {}).get("frontLeftTyrePressureKpa"),
    ),
    PolestarSensorEntityDescription(
        key="tyre_pressure_front_right",
        translation_key="tyre_pressure_front_right",
        native_unit_of_measurement=UnitOfPressure.KPA,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-tire-alert",
        value_fn=lambda data: (data.get("health") or {}).get("frontRightTyrePressureKpa"),
    ),
    PolestarSensorEntityDescription(
        key="tyre_pressure_rear_left",
        translation_key="tyre_pressure_rear_left",
        native_unit_of_measurement=UnitOfPressure.KPA,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-tire-alert",
        value_fn=lambda data: (data.get("health") or {}).get("rearLeftTyrePressureKpa"),
    ),
    PolestarSensorEntityDescription(
        key="tyre_pressure_rear_right",
        translation_key="tyre_pressure_rear_right",
        native_unit_of_measurement=UnitOfPressure.KPA,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-tire-alert",
        value_fn=lambda data: (data.get("health") or {}).get("rearRightTyrePressureKpa"),
    ),
    # Climate & Compartment
    PolestarSensorEntityDescription(
        key="compartment_temperature",
        translation_key="compartment_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("parking_climatization") or {}).get("currentCompartmentTemperatureCelsius"),
    ),
    PolestarSensorEntityDescription(
        key="requested_temperature",
        translation_key="requested_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:thermometer-auto",
        value_fn=lambda data: (data.get("parking_climatization") or {}).get("requestedCompartmentTemperatureCelsius"),
    ),
    PolestarSensorEntityDescription(
        key="climate_runtime_left",
        translation_key="climate_runtime_left",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        icon="mdi:timer-sand",
        value_fn=lambda data: (data.get("parking_climatization") or {}).get("runtimeLeftMinutes"),
    ),
    PolestarSensorEntityDescription(
        key="ventilation_mode",
        translation_key="ventilation_mode",
        device_class=SensorDeviceClass.ENUM,
        options=["neutral", "heating", "cooling", "off"],
        icon="mdi:fan",
        value_fn=lambda data: _clean_enum_value((data.get("parking_climatization") or {}).get("ventilation"), "VENTILATION_"),
    ),
    # Air Quality & Pre-cleaning
    PolestarSensorEntityDescription(
        key="measured_aqi",
        translation_key="measured_aqi",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("pre_cleaning") or {}).get("measuredAirQualityIndex"),
    ),
    PolestarSensorEntityDescription(
        key="measured_pm25",
        translation_key="measured_pm25",
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("pre_cleaning") or {}).get("measuredParticulateMatter25"),
    ),
    # Availability
    PolestarSensorEntityDescription(
        key="usage_mode",
        translation_key="usage_mode",
        device_class=SensorDeviceClass.ENUM,
        options=["abandoned", "parked", "driving", "convenience", "inactive"],
        icon="mdi:car-info",
        value_fn=lambda data: _clean_enum_value((data.get("availability") or {}).get("usageMode"), "USAGE_MODE_"),
    ),
    # Global Charge Timer Times
    PolestarSensorEntityDescription(
        key="global_charge_timer_start",
        translation_key="global_charge_timer_start",
        icon="mdi:clock-start",
        entity_registry_enabled_default=False,
        value_fn=lambda data: _format_time_obj(
            (data.get("global_charge_timer") or {}).get("globalChargeTimer", {}).get("start")
        ),
    ),
    PolestarSensorEntityDescription(
        key="global_charge_timer_stop",
        translation_key="global_charge_timer_stop",
        icon="mdi:clock-end",
        entity_registry_enabled_default=False,
        value_fn=lambda data: _format_time_obj(
            (data.get("global_charge_timer") or {}).get("globalChargeTimer", {}).get("stop")
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Polestar sensor entities based on a config entry."""
    coordinator: PolestarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PolestarSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class PolestarSensor(CoordinatorEntity[PolestarDataUpdateCoordinator], SensorEntity):
    """Representation of a Polestar sensor entity."""

    entity_description: PolestarSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PolestarDataUpdateCoordinator,
        description: PolestarSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.vin = coordinator.vin
        self._attr_unique_id = f"{coordinator.vin}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.vin)},
            name=f"Polestar ({coordinator.vin})",
            manufacturer="Polestar",
            model="Polestar 2",
            serial_number=coordinator.vin,
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
