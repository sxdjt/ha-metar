# HAMETAR - Home Assistant METAR Integration

A Home Assistant custom integration that fetches METAR aviation weather observations
from the [Aviation Weather Center](https://aviationweather.gov/) and exposes them as
sensor entities.

## Features

- Config flow UI - no YAML required
- One config entry per ICAO station; add as many stations as you like
- Configurable poll interval (default 5 minutes)
- Options flow to change the poll interval after setup
- Reconfigure flow to change the station without removing and re-adding
- 35 sensor entities covering all standard METAR fields

## Integration Quality 

HAMETAR meets the requirements for a [Silver rating](https://developers.home-assistant.io/docs/core/integration-quality-scale/) on the Home Assistant Integration Quality Scale.  While not a native HA integration, quality and assurance matters.  See the current [scorecard](SCORECARD.md) for test results and validation.

## Sensors

Sensors marked *disabled by default* are rarely reported and must be enabled manually in **Settings -> Devices & Services -> [station] -> entities**.

### Identification

| Sensor | Unit | Notes |
|--------|------|-------|
| Station Name | - | Full station name; diagnostic |

### Flight Conditions

| Sensor | Unit | Notes |
|--------|------|-------|
| Flight Category | - | VFR / MVFR / IFR / LIFR |

### Wind

| Sensor | Unit | Notes |
|--------|------|-------|
| Wind Speed | knots | |
| Wind Direction | degrees | `unknown` when variable (VRB); see `variable` attribute |
| Wind Gust | knots | `unknown` when no gust group reported |

### Visibility and Sky

| Sensor | Unit | Notes |
|--------|------|-------|
| Visibility | miles (statute) | Fractions parsed (e.g. 1/4 SM = 0.25) |
| Cloud Cover | - | Highest coverage layer: SKC / CLR / FEW / SCT / BKN / OVC / VV |
| Ceiling | feet | Lowest BKN, OVC, or VV layer; `unknown` when sky clear |
| Vertical Visibility | feet | Only reported when sky is obscured; *disabled by default* |

### Temperature

Both Celsius and Fahrenheit sensors are provided regardless of your HA unit system setting, so you can use whichever is appropriate for your automation.

| Sensor | Unit | Notes |
|--------|------|-------|
| Temperature | C | Pinned to Celsius |
| Temperature (F) | F | Pinned to Fahrenheit |
| Dewpoint | C | Pinned to Celsius |
| Dewpoint (F) | F | Pinned to Fahrenheit |
| Max Temperature (6 hr) | C | *Disabled by default*; diagnostic |
| Max Temperature (6 hr) (F) | F | *Disabled by default*; diagnostic |
| Min Temperature (6 hr) | C | *Disabled by default*; diagnostic |
| Min Temperature (6 hr) (F) | F | *Disabled by default*; diagnostic |
| Max Temperature (24 hr) | C | *Disabled by default*; diagnostic |
| Max Temperature (24 hr) (F) | F | *Disabled by default*; diagnostic |
| Min Temperature (24 hr) | C | *Disabled by default*; diagnostic |
| Min Temperature (24 hr) (F) | F | *Disabled by default*; diagnostic |

### Pressure

The altimeter setting is natively reported in both hPa and inHg. Both sensors are provided.

| Sensor | Unit | Notes |
|--------|------|-------|
| Altimeter | hPa | Pinned to hPa |
| Altimeter (inHg) | inHg | Pinned to inHg |
| Sea Level Pressure | hPa | |
| Pressure Tendency | hPa | Change over past 3 hours; *disabled by default*; diagnostic |

### Precipitation and Snow

| Sensor | Unit | Notes |
|--------|------|-------|
| Precipitation (1 hr) | inches | |
| Precipitation (3 hr) | inches | *Disabled by default*; diagnostic |
| Precipitation (6 hr) | inches | *Disabled by default*; diagnostic |
| Precipitation (24 hr) | inches | *Disabled by default*; diagnostic |
| Snow Depth | inches | *Disabled by default* |

### Metadata

| Sensor | Unit | Notes |
|--------|------|-------|
| Observation Time | - | Timestamp of the observation; rendered in local timezone |
| Report Type | - | `METAR` (routine) or `SPECI` (special); diagnostic |
| Station Elevation | feet | Static; diagnostic |
| Raw | - | Full raw METAR string; diagnostic |

## Extra State Attributes

Several sensors carry supplemental data as entity attributes.

### Flight Category

| Attribute | Description |
|-----------|-------------|
| `wx_string` | Decoded weather phenomena (e.g. `-RA BR`) |
| `report_time` | Observation timestamp from the API |
| `station_name` | Full station name |
| `clouds` | List of cloud layers: `[{"cover": "BKN", "base": 3000}, ...]` |

### Wind Direction

| Attribute | Description |
|-----------|-------------|
| `variable` | `true` when wind direction is variable (VRB) |

### Cloud Cover

| Attribute | Description |
|-----------|-------------|
| `layers` | List of all cloud layers: `[{"cover": "SCT", "base": 2500}, ...]` |

### Raw

| Attribute | Description |
|-----------|-------------|
| `report_time` | Observation timestamp |
| `receipt_time` | Time the observation was received by the API |
| `metar_type` | `METAR` or `SPECI` |

### Station Elevation

| Attribute | Description |
|-----------|-------------|
| `latitude` | Station latitude (decimal degrees) |
| `longitude` | Station longitude (decimal degrees) |

## Configuration

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| Station ID | Yes | - | ICAO station identifier, 3-4 alphanumeric characters (e.g. `KORD`, `EGLL`, `YSSY`). Must be a station with data in the Aviation Weather Center database. |
| Poll interval | No | 5 | How often to fetch a new observation, in minutes. Minimum 1, no maximum. METARs are issued roughly hourly; values below 5 minutes provide no additional data. |

The poll interval can be changed after setup via the integration's **Configure** option in Settings -> Devices & Services without removing and re-adding the station.

The station ID can be changed after setup via the **three-dot menu -> Reconfigure** option, which updates the station and reloads the integration.

## Installation

### Manual

1. Copy `custom_components/metar/` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings -> Devices & Services -> Add Integration** and search for **METAR**.
4. Enter the ICAO station identifier (e.g. `KORD`, `EGLL`, `YSSY`).
5. Set the poll interval in minutes (minimum 1, default 5).

### HACS

Add this repository as a custom HACS repository (type: Integration), then install from the HACS integrations page.

## Data Source

Data is fetched from:
```
https://aviationweather.gov/api/data/metar?ids={STATION}&format=json
```

No API key is required. The AWC asks that automated clients include a descriptive User-Agent; the integration uses the aiohttp session managed by Home Assistant.

## Flight Category Reference

| Category | Ceiling | Visibility |
|----------|---------|------------|
| VFR | >= 3000 ft | >= 5 SM |
| MVFR | 1000-2999 ft | 3-4.9 SM |
| IFR | 500-999 ft | 1-2.9 SM |
| LIFR | < 500 ft | < 1 SM |

The integration uses the category value returned directly by the AWC API.

## Removal

1. Go to **Settings -> Devices & Services**.
2. Find the **METAR** integration and click the three-dot menu next to the station entry.
3. Select **Delete**.
4. Restart Home Assistant (optional but recommended to fully clean up entities).
5. To completely remove the integration files, delete the `custom_components/metar/` directory from your Home Assistant configuration folder and restart.

## Contributing

Issues and pull requests are welcome.
