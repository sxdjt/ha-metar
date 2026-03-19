# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.1] - 2026-03-18

### Changed

- Station Elevation sensor is now disabled by default. It rarely changes and
  can be enabled manually if needed.

## [1.2.0] - 2026-03-16

### Changed

- Imports corrected to use canonical HA source modules for `DeviceInfo`
  (`homeassistant.helpers.device_registry`) and `EntityCategory`
  (`homeassistant.const`).
- All `dict` type annotations now fully parameterized (`dict[str, Any]`).

### Added

- `py.typed` PEP-561 marker enabling strict mypy type checking.
- Integration now meets Platinum level on the Home Assistant Integration
  Quality Scale (`strict-typing` rule satisfied; `async-dependency` exempt
  as there are no third-party pip dependencies; `inject-websession` done via
  direct use of `async_get_clientsession`).

## [1.1.0] - 2026-03-16

### Added

- New "Observation Time (Local)" sensor (`sensor.metar_{station}_obs_time_local`)
  showing the observation time converted to the system's local timezone.
- New "Time Since Observation" sensor (`sensor.metar_{station}_time_since_obs`)
  showing how many minutes have elapsed since the last reported observation.
- MIT license.

### Changed

- Integration display name changed from "METAR" to "HAMETAR".
- "Observation Time" sensor now displays the actual UTC timestamp string
  (e.g. `2026-03-14 23:35Z`) instead of a relative "x minutes ago" value.
- Renamed "Altimeter" sensor (hPa) to "QNH" (`sensor.metar_{station}_qnh`),
  reflecting the international standard term. The companion "Altimeter (inHg)"
  sensor is unchanged.

### Fixed

- Altimeter readings now correctly normalized to hPa for all stations. US stations
  report the A-group (inHg, e.g. A2992); international stations report the Q-group
  (hPa, e.g. Q1013). The integration parses the prefix from the raw METAR string
  and converts A-group values to hPa so that both the QNH (hPa) and
  Altimeter (inHg) sensors are accurate regardless of station origin.

## [1.0.1] - 2026-03-14

### Fixed

- Sensor entity IDs now follow the `sensor.metar_{station}_{key}` format
  (e.g. `sensor.metar_kpdx_wind_speed`) instead of the previous
  `sensor.{station}_{key}` format. Existing entities are automatically
  migrated on reload via the entity registry.

## [1.0.0] - 2026-03-13

### Added

- Initial release of HAMETAR
- Config flow UI setup with ICAO station ID validation
- Options flow to change poll interval after setup
- Reconfigure flow to change station ID without removing the integration
- DataUpdateCoordinator with proper error handling (timeout, HTTP errors, unavailable entities)
- 35 sensor entities per station:
  - Flight category (VFR / MVFR / IFR / LIFR)
  - Wind speed, direction, and gust
  - Visibility
  - Cloud cover and ceiling
  - Vertical visibility
  - Temperature and dewpoint (Celsius and Fahrenheit)
  - Max/min temperature 6-hour and 24-hour (Celsius and Fahrenheit)
  - Altimeter (hPa and inHg)
  - Sea level pressure
  - Pressure tendency
  - Precipitation 1-hour, 3-hour, 6-hour, and 24-hour
  - Snow depth
  - Observation time
  - Report type
  - Station name
  - Station elevation (with latitude/longitude attributes)
  - Raw METAR string
- Dual-unit sensors (Celsius/Fahrenheit, hPa/inHg) for temperature and pressure
- Extra state attributes on flight category, wind direction, cloud cover, raw, and station elevation
- Silver-level Integration Quality Scale compliance
- Diagnostics support
- pytest test suite covering config flow and coordinator
- Brand assets (icon and logo)
- HACS distribution support
