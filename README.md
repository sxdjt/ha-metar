# HAMETAR - Home Assistant METAR Integration

![GitHub Release](https://img.shields.io/github/v/release/sxdjt/ha-metar?style=for-the-badge)
[![AI Assisted](https://img.shields.io/badge/AI-Claude%20Code-AAAAAA.svg?style=for-the-badge)](https://claude.ai/code)
![GitHub License](https://img.shields.io/github/license/sxdjt/ha-metar?style=for-the-badge)

A Home Assistant custom integration that fetches METAR aviation weather observations
from the [Aviation Weather Center](https://aviationweather.gov/) and exposes them as
sensor entities.

## Features

- Config flow UI - no YAML required
- One config entry per ICAO station; add as many stations as you like
- Configurable poll interval (default 5 minutes)
- Options flow to change the poll interval after setup
- Reconfigure flow to change the station without removing and re-adding
- 37 sensor entities covering all standard METAR fields

## Integration Quality 

HAMETAR meets the requirements for a [Gold rating](https://developers.home-assistant.io/docs/core/integration-quality-scale/) on the Home Assistant Integration Quality Scale.  While not a native HA integration, quality and assurance matters.  See the current [scorecard](SCORECARD.md) for test results and validation.

## Configuration

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| Station ID | Yes | - | ICAO station identifier, 3-4 alphanumeric characters (e.g. `KORD`, `EGLL`, `YSSY`). Must be a station with data in the Aviation Weather Center database. |
| Poll interval | No | 5 | How often to fetch a new observation, in minutes. Minimum 1, maximum 10080 (1 week). METARs are issued roughly hourly; values below 5 minutes provide no additional data. |

## Installation

### HACS

Add this repository as a custom HACS repository (type: Integration), then install from the HACS integrations page.

## Sensors

Sensors marked *disabled by default* are rarely reported and must be enabled manually in **Settings -> Devices & Services -> [station] -> entities**.

## Example Sensor Output

# HAMETAR - Example Sensor Output

Station: **EDBB** (Berlin Tegel)
Sample observation: `EDBB 160950Z 25012KT 9999 FEW035 08/03 Q1018`

| Sensor | Value |
|--------|-------|
| `sensor.metar_edbb_station_name` | Berlin Tegel |
| `sensor.metar_edbb_altimeter_inhg` | 30.06 inHg |
| `sensor.metar_edbb_ceiling` | unavailable |
| `sensor.metar_edbb_cloud_cover` | FEW |
| `sensor.metar_edbb_dewpoint_f` | 37.4 F |
| `sensor.metar_edbb_dewpoint` | 3.0 C |
| `sensor.metar_edbb_elevation` | 122 ft |
| `sensor.metar_edbb_flight_category` | VFR |
| `sensor.metar_edbb_max_temp_24hr_f` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_max_temp_24hr` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_max_temp_6hr_f` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_max_temp_6hr` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_metar_type` | METAR |
| `sensor.metar_edbb_min_temp_24hr_f` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_min_temp_24hr` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_min_temp_6hr_f` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_min_temp_6hr` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_obs_time_local` | 2026-03-16 10:50 CET |
| `sensor.metar_edbb_obs_time` | 2026-03-16 09:50Z |
| `sensor.metar_edbb_precip_1hr` | unavailable |
| `sensor.metar_edbb_precip_24hr` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_precip_3hr` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_precip_6hr` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_pressure_tendency` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_qnh` | 1018.0 hPa |
| `sensor.metar_edbb_raw_metar` | EDBB 160950Z 25012KT 9999 FEW035 08/03 Q1018 |
| `sensor.metar_edbb_sea_level_pressure` | 1018.0 hPa |
| `sensor.metar_edbb_snow_depth` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_temperature_f` | 46.4 F |
| `sensor.metar_edbb_temperature` | 8.0 C |
| `sensor.metar_edbb_time_since_obs` | 12 min |
| `sensor.metar_edbb_vertical_visibility` | unavailable *(disabled by default)* |
| `sensor.metar_edbb_visibility` | 10+ SM |
| `sensor.metar_edbb_wind_direction` | 250 deg |
| `sensor.metar_edbb_wind_gust` | unavailable |
| `sensor.metar_edbb_wind_speed` | 12 kt |

**Notes:**
- "Disabled by default" - Entities are not commonly reported.  They exist in the registry but are off until manually enabled.
- `ceiling` is unavailable because the only cloud layer is FEW (no BKN/OVC/VV layer).
- `wind_gust` is unavailable because no gust group was reported.


## Sensor Details

### Identification

| Sensor | Unit | Type | Notes |
|--------|------|------|-------|
| Station Name | - | Raw | Full station name; diagnostic |

### Flight Conditions

| Sensor | Unit | Type | Notes |
|--------|------|------|-------|
| Flight Category | - | Raw | VFR / MVFR / IFR / LIFR |

### Wind

| Sensor | Unit | Type | Notes |
|--------|------|------|-------|
| Wind Speed | knots | Raw | |
| Wind Direction | degrees | Raw | `unknown` when variable (VRB); see `variable` attribute |
| Wind Gust | knots | Raw | `unknown` when no gust group reported |

### Visibility and Sky

| Sensor | Unit | Type | Notes |
|--------|------|------|-------|
| Visibility | miles (statute) | Calculated | String fractions parsed to decimal (e.g. 1/4 SM = 0.25) |
| Cloud Cover | - | Raw | Highest coverage layer: SKC / CLR / FEW / SCT / BKN / OVC / VV |
| Ceiling | feet | Calculated | Lowest BKN, OVC, or VV layer extracted from cloud layer list; `unknown` when sky clear |
| Vertical Visibility | feet | Raw | Only reported when sky is obscured; *disabled by default* |

### Temperature

Both Celsius and Fahrenheit sensors are provided regardless of your HA unit system setting, so you can use whichever is appropriate for your automation.

| Sensor | Unit | Type | Notes |
|--------|------|------|-------|
| Temperature | C | Raw | Pinned to Celsius |
| Temperature (F) | F | Calculated | Converted from Celsius |
| Dewpoint | C | Raw | Pinned to Celsius |
| Dewpoint (F) | F | Calculated | Converted from Celsius |
| Max Temperature (6 hr) | C | Raw | *Disabled by default*; diagnostic |
| Max Temperature (6 hr) (F) | F | Calculated | Converted from Celsius; *disabled by default*; diagnostic |
| Min Temperature (6 hr) | C | Raw | *Disabled by default*; diagnostic |
| Min Temperature (6 hr) (F) | F | Calculated | Converted from Celsius; *disabled by default*; diagnostic |
| Max Temperature (24 hr) | C | Raw | *Disabled by default*; diagnostic |
| Max Temperature (24 hr) (F) | F | Calculated | Converted from Celsius; *disabled by default*; diagnostic |
| Min Temperature (24 hr) | C | Raw | *Disabled by default*; diagnostic |
| Min Temperature (24 hr) (F) | F | Calculated | Converted from Celsius; *disabled by default*; diagnostic |

### Pressure

The QNH (altimeter setting) is always presented in both hPa and inHg. US stations report in inHg (A-group, e.g. A2992); international stations report in hPa (Q-group, e.g. Q1013). The integration normalizes to hPa internally and derives the inHg value, so both sensors are always available regardless of station origin.

| Sensor | Unit | Type | Notes |
|--------|------|------|-------|
| QNH | hPa | Calculated | Parsed from raw METAR string; A-group converted from inHg |
| Altimeter (inHg) | inHg | Calculated | Converted from hPa |
| Sea Level Pressure | hPa | Raw | |
| Pressure Tendency | hPa | Raw | Change over past 3 hours; *disabled by default*; diagnostic |

### Precipitation and Snow

| Sensor | Unit | Type | Notes |
|--------|------|------|-------|
| Precipitation (1 hr) | inches | Raw | |
| Precipitation (3 hr) | inches | Raw | *Disabled by default*; diagnostic |
| Precipitation (6 hr) | inches | Raw | *Disabled by default*; diagnostic |
| Precipitation (24 hr) | inches | Raw | *Disabled by default*; diagnostic |
| Snow Depth | inches | Raw | *Disabled by default* |

### Metadata

| Sensor | Unit | Type | Notes |
|--------|------|------|-------|
| Observation Time | - | Calculated | Unix epoch from API formatted as UTC timestamp string |
| Observation Time (Local) | - | Calculated | UTC observation time converted to system local timezone |
| Time Since Observation | minutes | Calculated | Elapsed minutes since the observation timestamp |
| Report Type | - | Raw | `METAR` (routine) or `SPECI` (special); diagnostic |
| Station Elevation | feet | Raw | Static; diagnostic |
| Raw | - | Raw | Full raw METAR string; diagnostic |

## Extra State Attributes

Several sensors carry supplemental data as entity attributes.

### Flight Category

| Attribute | Description | Type |
|-----------|-------------|------|
| `wx_string` | Decoded weather phenomena (e.g. `-RA BR`) | Raw |
| `report_time` | Observation timestamp from the API | Raw |
| `station_name` | Full station name | Raw |
| `clouds` | List of cloud layers: `[{"cover": "BKN", "base": 3000}, ...]` | Raw |

### Wind Direction

| Attribute | Description | Type |
|-----------|-------------|------|
| `variable` | `true` when wind direction is variable (VRB) | Calculated |

### Cloud Cover

| Attribute | Description | Type |
|-----------|-------------|------|
| `layers` | List of all cloud layers: `[{"cover": "SCT", "base": 2500}, ...]` | Raw |

### Raw

| Attribute | Description | Type |
|-----------|-------------|------|
| `report_time` | Observation timestamp | Raw |
| `receipt_time` | Time the observation was received by the API | Raw |
| `metar_type` | `METAR` or `SPECI` | Raw |

### Station Elevation

| Attribute | Description | Type |
|-----------|-------------|------|
| `latitude` | Station latitude (decimal degrees) | Raw |
| `longitude` | Station longitude (decimal degrees) | Raw |

## Data Source and Updates

Data is fetched from:
```
https://aviationweather.gov/api/data/metar?ids={STATION}&format=json
```

No API key is required. The AWC asks that automated clients include a descriptive User-Agent; the integration uses the aiohttp session managed by Home Assistant.  Data is retrieved every 5 minutes by default, but this can be configured between 1 minute and 10,080 (7 days).

## Example

A simple automation using HAMETAR data

```
automation:
    - alias: "EGLL freezing temperature alert"
      trigger:
        - platform: numeric_state
          entity_id: sensor.metar_egll_temperature_f
          below: 32
      action:
        - action: persistent_notification.create
          data:
            title: "Freezing Temperature at EGLL"
            message: >
              Temperature at EGLL is {{ states('sensor.metar_egll_temperature_f') }} F
              -- below freezing.
 ```

## Flight Category Reference

| Category | Ceiling | Visibility |
|----------|---------|------------|
| VFR | >= 3000 ft | >= 5 SM |
| MVFR | 1000-2999 ft | 3-4.9 SM |
| IFR | 500-999 ft | 1-2.9 SM |
| LIFR | < 500 ft | < 1 SM |

The integration uses the category value returned directly by the AWC API.

## Known Limitations

No known limitations other than requiring a valid ICAO airport station identifier and Internet access.

## Troubleshooting

The integration requires a valid [ICAO airport station identifier](https://opennav.com/airportcodes/icao).

### Station Not Found

Verify that you have entered a valid *ICAO* airport code, not a 3-letter IATA.

### Data Not Updating

The integration pulls whatever METAR is available for the station.  If the station has not issued an updated METAR, there are no changes.

### Entity values are "Unknown"

Some entities are not frequently reported, or are only reported when they are necessary.  An "Unavailable" entity means there was no data provided for it.


## Removal

1. Go to **Settings -> Devices & Services**.
2. Find the **HAMETAR** integration and click the three-dot menu next to the station entry.
3. Select **Delete**.
4. Restart Home Assistant (optional but recommended to fully clean up entities).
5. To completely remove the integration files, delete the `custom_components/hametar/` directory from your Home Assistant configuration folder and restart.

## Contributing

Issues and pull requests are welcome.

## License

This project is licensed under the [MIT License](LICENSE).
