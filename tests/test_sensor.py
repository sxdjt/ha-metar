"""Tests for the METAR sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.metar.sensor import (
    SENSOR_DESCRIPTIONS,
    MetarSensor,
    MetarSensorEntityDescription,
    _c_to_f,
    _hpa_to_inhg,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_coordinator(data=None, station_id="KORD"):
    """Return a minimal coordinator mock suitable for MetarSensor construction."""
    coord = MagicMock()
    coord.station_id = station_id
    coord.data = data
    coord.last_update_success = True
    # CoordinatorEntity registers a listener; return a no-op unsubscribe
    coord.async_add_listener = MagicMock(return_value=lambda: None)
    return coord


def make_sensor(key, data=None, station_id="KORD"):
    """Return a MetarSensor for the description with the given key."""
    coord = make_coordinator(data=data, station_id=station_id)
    desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == key)
    return MetarSensor(coord, desc)


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "c, expected_f",
    [
        (0.0, 32.0),
        (100.0, 212.0),
        (-40.0, -40.0),
        (18.3, 64.9),
    ],
)
def test_c_to_f(c, expected_f):
    assert _c_to_f(c) == pytest.approx(expected_f, abs=0.1)


def test_c_to_f_none():
    assert _c_to_f(None) is None


def test_hpa_to_inhg_normal():
    # 1013.25 hPa is the standard atmosphere = 29.921 inHg
    assert _hpa_to_inhg(1013.25) == pytest.approx(29.92, rel=0.001)


def test_hpa_to_inhg_none():
    assert _hpa_to_inhg(None) is None


# ---------------------------------------------------------------------------
# MetarSensor initialization
# ---------------------------------------------------------------------------


def test_sensor_unique_id():
    sensor = make_sensor("temperature")
    assert sensor._attr_unique_id == "KORD_temperature"


def test_sensor_unique_id_uses_station_id():
    sensor = make_sensor("altimeter", station_id="EGLL")
    assert sensor._attr_unique_id == "EGLL_altimeter"


def test_sensor_name_is_entity_portion_only():
    """With has_entity_name=True, _attr_name must not include the station ID."""
    sensor = make_sensor("temperature")
    assert sensor._attr_name == "Temperature"
    assert "KORD" not in (sensor._attr_name or "")


def test_sensor_station_name_field_label_only():
    """Station name sensor should have field-only name (device name prepended by HA)."""
    sensor = make_sensor("station_name")
    assert sensor._attr_name == "Station Name"
    assert "KORD" not in (sensor._attr_name or "")


def test_sensor_suggested_object_id():
    # HA prepends the device name slug ("metar_kord") to this, giving
    # entity IDs like sensor.metar_kord_temperature.
    sensor = make_sensor("temperature")
    assert sensor.suggested_object_id == "temperature"


def test_sensor_suggested_object_id_different_station():
    sensor = make_sensor("altimeter", station_id="EGLL")
    assert sensor.suggested_object_id == "altimeter"


def test_sensor_suggested_object_id_no_station_prefix():
    sensor = make_sensor("wind_speed", station_id="PANC")
    assert sensor.suggested_object_id == "wind_speed"


# ---------------------------------------------------------------------------
# native_value
# ---------------------------------------------------------------------------


def test_native_value_temperature():
    sensor = make_sensor("temperature", data={"temperature": 18.3})
    assert sensor.native_value == pytest.approx(18.3)


def test_native_value_when_data_is_none():
    sensor = make_sensor("temperature", data=None)
    assert sensor.native_value is None


def test_native_value_when_field_missing():
    # wind_gust is None when not reported
    sensor = make_sensor("wind_gust", data={"wind_gust": None})
    assert sensor.native_value is None


def test_native_value_temperature_f():
    sensor = make_sensor("temperature_f", data={"temperature": 0.0})
    assert sensor.native_value == pytest.approx(32.0)


def test_native_value_dewpoint_f():
    sensor = make_sensor("dewpoint_f", data={"dewpoint": 10.0})
    assert sensor.native_value == pytest.approx(50.0)


def test_native_value_altimeter_hpa():
    sensor = make_sensor("altimeter", data={"altimeter": 1013.2})
    assert sensor.native_value == pytest.approx(1013.2)


def test_native_value_altimeter_inhg():
    sensor = make_sensor("altimeter_inhg", data={"altimeter": 1013.25})
    assert sensor.native_value == pytest.approx(29.92, rel=0.001)


def test_native_value_flight_category():
    sensor = make_sensor("flight_category", data={"flight_category": "VFR"})
    assert sensor.native_value == "VFR"


def test_native_value_visibility():
    sensor = make_sensor("visibility", data={"visibility": 10.0})
    assert sensor.native_value == pytest.approx(10.0)


def test_native_value_max_temp_6hr_f():
    sensor = make_sensor("max_temp_6hr_f", data={"max_temp_6hr": -40.0})
    assert sensor.native_value == pytest.approx(-40.0)


def test_native_value_min_temp_6hr_f():
    sensor = make_sensor("min_temp_6hr_f", data={"min_temp_6hr": 100.0})
    assert sensor.native_value == pytest.approx(212.0)


def test_native_value_max_temp_24hr_f():
    sensor = make_sensor("max_temp_24hr_f", data={"max_temp_24hr": 0.0})
    assert sensor.native_value == pytest.approx(32.0)


def test_native_value_min_temp_24hr_f():
    sensor = make_sensor("min_temp_24hr_f", data={"min_temp_24hr": 0.0})
    assert sensor.native_value == pytest.approx(32.0)


# ---------------------------------------------------------------------------
# extra_state_attributes
# ---------------------------------------------------------------------------


def test_extra_attrs_when_data_none():
    sensor = make_sensor("flight_category", data=None)
    assert sensor.extra_state_attributes == {}


def test_extra_attrs_flight_category():
    data = {
        "wx_string": "-RA",
        "report_time": "2024-01-01T00:00:00Z",
        "station_name": "Chicago O Hare",
        "clouds": [{"cover": "OVC", "base": 800}],
    }
    sensor = make_sensor("flight_category", data=data)
    attrs = sensor.extra_state_attributes
    assert attrs["wx_string"] == "-RA"
    assert attrs["report_time"] == "2024-01-01T00:00:00Z"
    assert attrs["station_name"] == "Chicago O Hare"
    assert attrs["clouds"] == data["clouds"]


def test_extra_attrs_wind_direction_not_variable():
    sensor = make_sensor("wind_direction", data={"wind_variable": False})
    assert sensor.extra_state_attributes == {"variable": False}


def test_extra_attrs_wind_direction_variable():
    sensor = make_sensor("wind_direction", data={"wind_variable": True})
    assert sensor.extra_state_attributes == {"variable": True}


def test_extra_attrs_cloud_cover():
    data = {"clouds": [{"cover": "BKN", "base": 3000}]}
    sensor = make_sensor("cloud_cover", data=data)
    assert sensor.extra_state_attributes == {"layers": data["clouds"]}


def test_extra_attrs_raw_metar():
    data = {
        "report_time": "2024-01-01T00:00:00Z",
        "receipt_time": "2024-01-01T00:01:00Z",
        "metar_type": "METAR",
    }
    sensor = make_sensor("raw_metar", data=data)
    attrs = sensor.extra_state_attributes
    assert attrs["report_time"] == "2024-01-01T00:00:00Z"
    assert attrs["receipt_time"] == "2024-01-01T00:01:00Z"
    assert attrs["metar_type"] == "METAR"


def test_extra_attrs_elevation():
    data = {"latitude": 41.98, "longitude": -87.91}
    sensor = make_sensor("elevation", data=data)
    attrs = sensor.extra_state_attributes
    assert attrs["latitude"] == pytest.approx(41.98)
    assert attrs["longitude"] == pytest.approx(-87.91)


def test_extra_attrs_default_empty_for_other_sensors():
    """Sensors without special attributes return an empty dict."""
    sensor = make_sensor("visibility", data={"visibility": 10.0})
    assert sensor.extra_state_attributes == {}


def test_extra_attrs_temperature_no_extras():
    sensor = make_sensor("temperature", data={"temperature": 20.0})
    assert sensor.extra_state_attributes == {}


# ---------------------------------------------------------------------------
# SENSOR_DESCRIPTIONS integrity
# ---------------------------------------------------------------------------


def test_sensor_descriptions_are_non_empty():
    assert len(SENSOR_DESCRIPTIONS) >= 20


def test_all_descriptions_have_callable_value_fn():
    for desc in SENSOR_DESCRIPTIONS:
        assert callable(desc.value_fn), f"No callable value_fn for key={desc.key}"


def test_all_descriptions_have_unique_keys():
    keys = [desc.key for desc in SENSOR_DESCRIPTIONS]
    assert len(keys) == len(set(keys)), "Duplicate keys in SENSOR_DESCRIPTIONS"


def test_all_descriptions_have_name():
    for desc in SENSOR_DESCRIPTIONS:
        assert desc.name, f"Empty name for key={desc.key}"


# ---------------------------------------------------------------------------
# entity_registry_enabled_default
# ---------------------------------------------------------------------------

_DISABLED_BY_DEFAULT = {
    "vertical_visibility",
    "max_temp_6hr", "max_temp_6hr_f",
    "min_temp_6hr", "min_temp_6hr_f",
    "max_temp_24hr", "max_temp_24hr_f",
    "min_temp_24hr", "min_temp_24hr_f",
    "pressure_tendency",
    "precip_3hr", "precip_6hr", "precip_24hr",
    "snow_depth",
}

_ENABLED_BY_DEFAULT = {
    "station_name", "flight_category", "wind_speed", "wind_direction",
    "wind_gust", "visibility", "cloud_cover", "ceiling",
    "temperature", "temperature_f", "dewpoint", "dewpoint_f",
    "altimeter", "altimeter_inhg", "sea_level_pressure",
    "precip_1hr", "obs_time", "metar_type", "elevation", "raw_metar",
}


def test_rarely_reported_sensors_disabled_by_default():
    for desc in SENSOR_DESCRIPTIONS:
        if desc.key in _DISABLED_BY_DEFAULT:
            assert desc.entity_registry_enabled_default is False, (
                f"{desc.key} should be disabled by default"
            )


def test_primary_sensors_enabled_by_default():
    for desc in SENSOR_DESCRIPTIONS:
        if desc.key in _ENABLED_BY_DEFAULT:
            # entity_registry_enabled_default defaults to True when not set
            assert desc.entity_registry_enabled_default is not False, (
                f"{desc.key} should be enabled by default"
            )


# ---------------------------------------------------------------------------
# async_setup_entry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_setup_entry_creates_all_sensors():
    """async_setup_entry adds one MetarSensor per description."""
    from homeassistant.core import HomeAssistant

    hass = MagicMock(spec=HomeAssistant)
    coordinator = make_coordinator(data={})

    entry = MagicMock()
    entry.runtime_data = coordinator

    added = []
    async_add_entities = MagicMock(side_effect=lambda entities: added.extend(list(entities)))

    from custom_components.metar.sensor import async_setup_entry
    await async_setup_entry(hass, entry, async_add_entities)

    async_add_entities.assert_called_once()
    assert len(added) == len(SENSOR_DESCRIPTIONS)
    assert all(isinstance(s, MetarSensor) for s in added)
