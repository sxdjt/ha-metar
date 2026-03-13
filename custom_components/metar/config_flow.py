"""Config flow for the METAR integration."""

from __future__ import annotations

import logging
import re

import voluptuous as vol
from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    AWC_METAR_URL,
    CONF_STATION_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# ICAO station identifiers are 3-4 uppercase letters (some non-US stations use 3)
_STATION_RE = re.compile(r"^[A-Z0-9]{3,4}$")


def _station_schema(default_station: str = "") -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_STATION_ID, default=default_station): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                int, vol.Range(min=MIN_SCAN_INTERVAL)
            ),
        }
    )


def _options_schema(current_interval: int) -> vol.Schema:
    return vol.Schema(
        {
            vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                int, vol.Range(min=MIN_SCAN_INTERVAL)
            ),
        }
    )


async def _validate_station(hass, station_id: str) -> str | None:
    """Return an error key if the station ID is invalid or unreachable.

    Returns None on success.
    """
    station_id = station_id.strip().upper()
    if not _STATION_RE.match(station_id):
        return "invalid_station_format"

    session = async_get_clientsession(hass)
    try:
        async with session.get(
            AWC_METAR_URL,
            params={"ids": station_id, "format": "json"},
        ) as response:
            if response.status != 200:
                return "cannot_connect"
            data = await response.json()
            if not data or not isinstance(data, list):
                return "station_not_found"
    except ClientError:
        return "cannot_connect"

    return None


class MetarConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for METAR."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> MetarOptionsFlow:
        """Return the options flow handler."""
        return MetarOptionsFlow()

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            station_id = user_input[CONF_STATION_ID].strip().upper()
            error = await _validate_station(self.hass, station_id)
            if error:
                errors["base"] = error
            else:
                # Prevent duplicate entries for the same station
                await self.async_set_unique_id(station_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=station_id,
                    data={
                        CONF_STATION_ID: station_id,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_station_schema(),
            errors=errors,
        )


class MetarOptionsFlow(OptionsFlow):
    """Handle options for an existing METAR config entry."""

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Manage the options."""
        current_interval = self.config_entry.data.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        # Options override data when present
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, current_interval
        )

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(current_interval),
        )
