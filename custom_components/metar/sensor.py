"""Sensor platform for the METAR integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MetarCoordinator
from .entity import MetarEntity

# Coordinator-based platform: all entities update from the shared coordinator,
# so no parallel polling of individual entities is needed.
PARALLEL_UPDATES = 0


def _c_to_f(celsius: float | None) -> float | None:
    """Convert Celsius to Fahrenheit, rounded to one decimal place."""
    if celsius is None:
        return None
    return round(celsius * 9 / 5 + 32, 1)


def _hpa_to_inhg(hpa: float | None) -> float | None:
    """Convert hectopascals to inches of mercury, rounded to two decimal places."""
    if hpa is None:
        return None
    return round(hpa * 0.02953, 2)


@dataclass(frozen=True, kw_only=True)
class MetarSensorEntityDescription(SensorEntityDescription):
    """Extends SensorEntityDescription with a value extractor function.

    value_fn receives the normalized coordinator data dict and returns the
    sensor's native value (or None when the field is absent/not reported).
    station_prefix controls whether the station ID is prepended to the display
    name (default True). Set to False for sensors whose name is self-contained.
    """

    value_fn: Callable[[dict], Any]
    station_prefix: bool = True


# ---------------------------------------------------------------------------
# Sensor definitions
# One entry per sensor entity created for each configured station.
# Fields that are not reported in a given observation return None, which HA
# displays as "unavailable" — correct behaviour for optional METAR groups.
# ---------------------------------------------------------------------------

SENSOR_DESCRIPTIONS: tuple[MetarSensorEntityDescription, ...] = (

    # --- Station identification ---
    MetarSensorEntityDescription(
        key="station_name",
        name="Station Name",
        icon="mdi:map-marker",
        entity_category=EntityCategory.DIAGNOSTIC,
        station_prefix=False,
        value_fn=lambda d: d.get("station_name"),
    ),

    # --- Flight category ---
    MetarSensorEntityDescription(
        key="flight_category",
        name="Flight Category",
        icon="mdi:airplane",
        value_fn=lambda d: d.get("flight_category"),
    ),

    # --- Wind ---
    MetarSensorEntityDescription(
        key="wind_speed",
        name="Wind Speed",
        icon="mdi:weather-windy",
        native_unit_of_measurement=UnitOfSpeed.KNOTS,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("wind_speed"),
    ),
    MetarSensorEntityDescription(
        key="wind_direction",
        name="Wind Direction",
        icon="mdi:compass-rose",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        # None when wind is variable (VRB); see the "variable" extra attribute.
        value_fn=lambda d: d.get("wind_direction"),
    ),
    MetarSensorEntityDescription(
        key="wind_gust",
        name="Wind Gust",
        icon="mdi:weather-windy-variant",
        native_unit_of_measurement=UnitOfSpeed.KNOTS,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        # None (unavailable) when no gust group is present in the METAR
        value_fn=lambda d: d.get("wind_gust"),
    ),

    # --- Visibility ---
    MetarSensorEntityDescription(
        key="visibility",
        name="Visibility",
        icon="mdi:eye",
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("visibility"),
    ),

    # --- Sky / clouds ---
    MetarSensorEntityDescription(
        key="cloud_cover",
        name="Cloud Cover",
        icon="mdi:weather-cloudy",
        # Categorical: SKC / CLR / FEW / SCT / BKN / OVC / VV
        value_fn=lambda d: d.get("cloud_cover"),
    ),
    MetarSensorEntityDescription(
        key="ceiling",
        name="Ceiling",
        icon="mdi:weather-cloudy-arrow-right",
        native_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        # None (unavailable) when there is no BKN, OVC, or VV layer
        value_fn=lambda d: d.get("ceiling"),
    ),
    MetarSensorEntityDescription(
        key="vertical_visibility",
        name="Vertical Visibility",
        icon="mdi:arrow-up-thin",
        native_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        # Reported only when sky is obscured (VV group replaces cloud layers)
        value_fn=lambda d: d.get("vertical_visibility"),
    ),

    # --- Temperature ---
    # Celsius pairs: METAR natively reports temperatures in Celsius.
    # Fahrenheit pairs added so both units are always available regardless of
    # the HA system unit setting.
    MetarSensorEntityDescription(
        key="temperature",
        name="Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("temperature"),
    ),
    MetarSensorEntityDescription(
        key="temperature_f",
        name="Temperature (F)",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        suggested_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _c_to_f(d.get("temperature")),
    ),
    MetarSensorEntityDescription(
        key="dewpoint",
        name="Dewpoint",
        icon="mdi:thermometer-water",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("dewpoint"),
    ),
    MetarSensorEntityDescription(
        key="dewpoint_f",
        name="Dewpoint (F)",
        icon="mdi:thermometer-water",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        suggested_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _c_to_f(d.get("dewpoint")),
    ),
    MetarSensorEntityDescription(
        key="max_temp_6hr",
        name="Max Temperature (6 hr)",
        icon="mdi:thermometer-chevron-up",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("max_temp_6hr"),
    ),
    MetarSensorEntityDescription(
        key="max_temp_6hr_f",
        name="Max Temperature (6 hr) (F)",
        icon="mdi:thermometer-chevron-up",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        suggested_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _c_to_f(d.get("max_temp_6hr")),
    ),
    MetarSensorEntityDescription(
        key="min_temp_6hr",
        name="Min Temperature (6 hr)",
        icon="mdi:thermometer-chevron-down",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("min_temp_6hr"),
    ),
    MetarSensorEntityDescription(
        key="min_temp_6hr_f",
        name="Min Temperature (6 hr) (F)",
        icon="mdi:thermometer-chevron-down",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        suggested_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _c_to_f(d.get("min_temp_6hr")),
    ),
    MetarSensorEntityDescription(
        key="max_temp_24hr",
        name="Max Temperature (24 hr)",
        icon="mdi:thermometer-chevron-up",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("max_temp_24hr"),
    ),
    MetarSensorEntityDescription(
        key="max_temp_24hr_f",
        name="Max Temperature (24 hr) (F)",
        icon="mdi:thermometer-chevron-up",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        suggested_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _c_to_f(d.get("max_temp_24hr")),
    ),
    MetarSensorEntityDescription(
        key="min_temp_24hr",
        name="Min Temperature (24 hr)",
        icon="mdi:thermometer-chevron-down",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("min_temp_24hr"),
    ),
    MetarSensorEntityDescription(
        key="min_temp_24hr_f",
        name="Min Temperature (24 hr) (F)",
        icon="mdi:thermometer-chevron-down",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        suggested_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _c_to_f(d.get("min_temp_24hr")),
    ),

    # --- Pressure ---
    # Altimeter setting: the AWC JSON API returns hPa, but the METAR A-group
    # (e.g. A2992) is natively in inHg — that is what pilots dial into their
    # altimeters. Both units are provided.
    MetarSensorEntityDescription(
        key="altimeter",
        name="Altimeter",
        icon="mdi:gauge",
        native_unit_of_measurement=UnitOfPressure.HPA,
        suggested_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("altimeter"),
    ),
    MetarSensorEntityDescription(
        key="altimeter_inhg",
        name="Altimeter (inHg)",
        icon="mdi:gauge",
        native_unit_of_measurement=UnitOfPressure.INHG,
        suggested_unit_of_measurement=UnitOfPressure.INHG,
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _hpa_to_inhg(d.get("altimeter")),
    ),
    MetarSensorEntityDescription(
        key="sea_level_pressure",
        name="Sea Level Pressure",
        icon="mdi:gauge-low",
        native_unit_of_measurement=UnitOfPressure.HPA,
        suggested_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("sea_level_pressure"),
    ),
    MetarSensorEntityDescription(
        key="pressure_tendency",
        name="Pressure Tendency",
        icon="mdi:gauge",
        native_unit_of_measurement=UnitOfPressure.HPA,
        # Positive = rising, negative = falling over the past 3 hours
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("pressure_tendency"),
    ),

    # --- Precipitation ---
    MetarSensorEntityDescription(
        key="precip_1hr",
        name="Precipitation (1 hr)",
        icon="mdi:weather-rainy",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("precip_1hr"),
    ),
    MetarSensorEntityDescription(
        key="precip_3hr",
        name="Precipitation (3 hr)",
        icon="mdi:weather-rainy",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("precip_3hr"),
    ),
    MetarSensorEntityDescription(
        key="precip_6hr",
        name="Precipitation (6 hr)",
        icon="mdi:weather-rainy",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("precip_6hr"),
    ),
    MetarSensorEntityDescription(
        key="precip_24hr",
        name="Precipitation (24 hr)",
        icon="mdi:weather-rainy",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("precip_24hr"),
    ),
    MetarSensorEntityDescription(
        key="snow_depth",
        name="Snow Depth",
        icon="mdi:snowflake",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("snow_depth"),
    ),

    # --- Observation time ---
    MetarSensorEntityDescription(
        key="obs_time",
        name="Observation Time",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        # Returns an aware datetime; HA renders it in the user's local timezone.
        value_fn=lambda d: d.get("obs_time"),
    ),

    # --- Report type ---
    MetarSensorEntityDescription(
        key="metar_type",
        name="Report Type",
        icon="mdi:file-document-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        # "METAR" (routine) or "SPECI" (special observation)
        value_fn=lambda d: d.get("metar_type"),
    ),

    # --- Station location (static, diagnostic) ---
    MetarSensorEntityDescription(
        key="elevation",
        name="Station Elevation",
        icon="mdi:elevation-rise",
        native_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("elevation"),
    ),

    # --- Raw observation string ---
    MetarSensorEntityDescription(
        key="raw_metar",
        name="Raw",
        icon="mdi:text",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("raw_metar"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up METAR sensors from a config entry."""
    coordinator: MetarCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        MetarSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class MetarSensor(MetarEntity, SensorEntity):
    """A single METAR sensor entity backed by the shared coordinator."""

    entity_description: MetarSensorEntityDescription

    def __init__(
        self,
        coordinator: MetarCoordinator,
        description: MetarSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.station_id}_{description.key}"
        # Full display name: "EGLL Altimeter" by default, or just the bare name
        # when station_prefix=False (e.g. "Station Name").
        if description.station_prefix:
            self._attr_name = f"{coordinator.station_id} {description.name}"
        else:
            self._attr_name = description.name

    @property
    def suggested_object_id(self) -> str:
        """Return the suggested entity ID suffix: egll_metar_altimeter, etc."""
        return (
            f"{self.coordinator.station_id.lower()}_metar_{self.entity_description.key}"
        )

    @property
    def native_value(self) -> Any:
        """Return the current sensor value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes for sensors that benefit from supplemental data."""
        if self.coordinator.data is None:
            return {}

        data = self.coordinator.data
        key = self.entity_description.key

        if key == "flight_category":
            return {
                "wx_string": data.get("wx_string"),
                "report_time": data.get("report_time"),
                "station_name": data.get("station_name"),
                "clouds": data.get("clouds", []),
            }

        if key == "wind_direction":
            # Lets automations distinguish VRB (variable) from a true 0-degree reading
            return {"variable": data.get("wind_variable", False)}

        if key == "cloud_cover":
            return {"layers": data.get("clouds", [])}

        if key == "raw_metar":
            return {
                "report_time": data.get("report_time"),
                "receipt_time": data.get("receipt_time"),
                "metar_type": data.get("metar_type"),
            }

        if key == "elevation":
            return {
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
            }

        return {}
