# HAMETAR - Home Assistant Custom Integration

A Home Assistant custom integration that fetches METAR aviation weather observations
from the [Aviation Weather Center](https://aviationweather.gov/) and exposes them as
sensor entities.

## Features

- Config flow UI - no YAML required
- One config entry per ICAO station; add as many stations as you like
- Configurable poll interval (default 5 minutes)
- Options flow to change the poll interval after setup
- Sensor entities for all key METAR fields

## Sensors

| Entity | Unit | Notes |
|--------|------|-------|
| Flight Category | - | VFR / MVFR / IFR / LIFR |
| Wind Speed | knots | |
| Wind Direction | degrees | `variable: true` attribute when VRB |
| Wind Gust | knots | `unknown` when no gust reported |
| Visibility | miles (statute) | Fractions parsed (e.g. 1/4 SM) |
| Ceiling | feet | Lowest BKN/OVC/VV layer; `unknown` when clear |
| Temperature | C | HA converts to your preferred unit |
| Dewpoint | C | |
| Altimeter | inHg | |
| Raw METAR | - | Full raw observation string (diagnostic) |

The `flight_category` sensor also carries these extra attributes:
- `wx_string` - decoded weather phenomena (e.g. `-RA BR`)
- `report_time` - observation timestamp from the API
- `station_name` - full station name
- `clouds` - list of cloud layer objects `[{cover, base}, ...]`

## Configuration

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| Station ID | Yes | - | ICAO station identifier, 3-4 alphanumeric characters (e.g. `KORD`, `EGLL`, `YSSY`). Must be a station with data in the Aviation Weather Center database. |
| Poll interval | No | 5 | How often to fetch a new observation, in minutes. Minimum 1, no maximum. METARs are issued roughly hourly; values below 5 minutes provide no additional data. |

The poll interval can be changed after setup via the integration's **Configure** option in Settings -> Devices & Services without removing and re-adding the station.

## Installation

### Manual

1. Copy `custom_components/metar/` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings -> Devices & Services -> Add Integration** and search for **METAR**.
4. Enter the ICAO station identifier (e.g. `KORD`, `EGLL`, `YSSY`).
5. Set the poll interval in minutes (minimum 1, default 5).

### HACS

Add this repository as a custom HACS repository (type: Integration), then install
from the HACS integrations page.

## Data Source

Data is fetched from:
```
https://aviationweather.gov/api/data/metar?ids={STATION}&format=json
```

No API key is required. The AWC asks that automated clients include a descriptive
User-Agent; the integration uses the aiohttp session managed by Home Assistant.

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
