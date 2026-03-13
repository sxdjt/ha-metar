"""DataUpdateCoordinator for the METAR integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from datetime import timedelta

import aiohttp
from aiohttp import ClientError, ClientResponseError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import ATTRIBUTION, AWC_METAR_URL, CEILING_LAYERS, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _parse_visibility(raw: str | float | int | None) -> float | None:
    """Convert the AWC visibility field to a float in statute miles.

    The API returns values such as "10+", "6", "1/2", "1 1/4", or a plain number.
    Values ending with "+" mean "greater than X"; we return X in that case.
    Returns None if the value cannot be parsed.
    """
    if raw is None:
        return None
    text = str(raw).strip().rstrip("+")
    parts = text.split()
    try:
        if len(parts) == 2:
            # "1 1/2" style — whole number followed by a fraction
            whole = float(parts[0])
            num, den = parts[1].split("/")
            return round(whole + float(num) / float(den), 2)
        if "/" in parts[0]:
            num, den = parts[0].split("/")
            return round(float(num) / float(den), 2)
        return float(parts[0])
    except (ValueError, ZeroDivisionError):
        _LOGGER.debug("Could not parse visibility value: %r", raw)
        return None


def _extract_ceiling(clouds: list[dict] | None) -> int | None:
    """Return the height (feet) of the lowest BKN, OVC, or VV cloud layer.

    Returns None when the sky is clear or no ceiling layer is present.
    """
    if not clouds:
        return None
    ceiling = None
    for layer in clouds:
        cover = layer.get("cover", "")
        base = layer.get("base")
        if cover in CEILING_LAYERS and base is not None:
            if ceiling is None or base < ceiling:
                ceiling = int(base)
    return ceiling


def _obs_time_to_dt(obs_time: int | None) -> datetime | None:
    """Convert the obsTime Unix epoch integer to a UTC-aware datetime, or None."""
    if obs_time is None:
        return None
    try:
        return datetime.fromtimestamp(int(obs_time), tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


class MetarCoordinator(DataUpdateCoordinator[dict]):
    """Fetch METAR data from the Aviation Weather Center API."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str,
        scan_interval: int,
    ) -> None:
        """Set up the coordinator."""
        self.station_id = station_id.upper()
        self.attribution = ATTRIBUTION
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.station_id}",
            update_interval=timedelta(minutes=scan_interval),
        )

    async def _async_update_data(self) -> dict:
        """Fetch the latest METAR observation and return a normalized dict."""
        params = {"ids": self.station_id, "format": "json"}
        session = async_get_clientsession(self.hass)

        timeout = aiohttp.ClientTimeout(total=30)
        try:
            async with session.get(
                AWC_METAR_URL, params=params, timeout=timeout
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except asyncio.TimeoutError as err:
            raise UpdateFailed(
                f"Timeout fetching METAR for {self.station_id}"
            ) from err
        except ClientResponseError as err:
            raise UpdateFailed(
                f"HTTP {err.status} fetching METAR for {self.station_id}"
            ) from err
        except ClientError as err:
            raise UpdateFailed(
                f"Network error fetching METAR for {self.station_id}: {err}"
            ) from err

        if not data or not isinstance(data, list):
            raise UpdateFailed(
                f"No METAR data returned for station {self.station_id}"
            )

        return self._normalize(data[0])

    def _normalize(self, raw: dict) -> dict:  # noqa: PLR0912
        """Extract and coerce every field from the raw API response.

        All keys are kept even when None so that sensors can reliably
        check for their key rather than guarding against KeyError.
        """
        clouds = raw.get("clouds") or []

        # Wind direction may be an integer degrees value or the string "VRB"
        wdir_raw = raw.get("wdir")
        if wdir_raw == "VRB" or wdir_raw is None:
            wind_direction = None
            wind_variable = wdir_raw == "VRB"
        else:
            wind_direction = int(wdir_raw)
            wind_variable = False

        # obsTime is a Unix epoch integer; convert to an aware datetime for HA
        obs_dt = _obs_time_to_dt(raw.get("obsTime"))

        return {
            # --- Identification ---
            "station_id": raw.get("icaoId", self.station_id),
            "station_name": raw.get("name"),
            "metar_type": raw.get("metarType"),          # "METAR" or "SPECI"

            # --- Observation timestamps ---
            "obs_time": obs_dt,                          # aware datetime or None
            "report_time": raw.get("reportTime"),        # ISO string from API
            "receipt_time": raw.get("receiptTime"),      # ISO string from API

            # --- Flight category ---
            "flight_category": raw.get("fltCat"),        # VFR / MVFR / IFR / LIFR

            # --- Wind ---
            "wind_direction": wind_direction,            # degrees (int) or None when VRB
            "wind_variable": wind_variable,              # True when direction is VRB
            "wind_speed": raw.get("wspd"),               # knots int or None
            "wind_gust": raw.get("wgst"),                # knots int or None (absent = no gust)

            # --- Visibility ---
            "visibility": _parse_visibility(raw.get("visib")),  # statute miles float

            # --- Sky / clouds ---
            "cloud_cover": raw.get("cover"),             # overall cover code (SCT, BKN, etc.)
            "ceiling": _extract_ceiling(clouds),         # feet of lowest BKN/OVC/VV, or None
            "clouds": clouds,                            # full layer list for attributes

            # --- Temperature ---
            "temperature": raw.get("temp"),              # Celsius float or None
            "dewpoint": raw.get("dewp"),                 # Celsius float or None

            # --- Pressure ---
            "altimeter": raw.get("altim"),               # hPa float (API field, despite name)
            "sea_level_pressure": raw.get("slp"),        # hPa float or None

            # --- Precipitation (6-hourly groups, None when not reported) ---
            "precip_1hr": raw.get("precip"),             # inches
            "precip_3hr": raw.get("pcp3hr"),             # inches
            "precip_6hr": raw.get("pcp6hr"),             # inches
            "precip_24hr": raw.get("pcp24hr"),           # inches
            "snow_depth": raw.get("snow"),               # inches

            # --- Other reported values ---
            "max_temp_6hr": raw.get("maxT"),             # Celsius, 6-hour max
            "min_temp_6hr": raw.get("minT"),             # Celsius, 6-hour min
            "max_temp_24hr": raw.get("maxT24"),          # Celsius, 24-hour max
            "min_temp_24hr": raw.get("minT24"),          # Celsius, 24-hour min
            "pressure_tendency": raw.get("presTend"),    # hPa/3hr (pos = rising)
            "vertical_visibility": raw.get("vertVis"),   # feet, when sky obscured

            # --- Weather phenomena string (e.g. "-RA BR") ---
            "wx_string": raw.get("wxString") or None,

            # --- Station location (static, but included for completeness) ---
            "latitude": raw.get("lat"),
            "longitude": raw.get("lon"),
            "elevation": raw.get("elev"),                # feet MSL

            # --- Raw observation ---
            "raw_metar": raw.get("rawOb"),
        }
