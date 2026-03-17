"""Config flow for the METAR integration."""

from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol
from aiohttp import ClientError, ContentTypeError

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    AWC_METAR_URL,
    CONF_STATION_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# ICAO station identifiers are 3-4 uppercase letters (some non-US stations use 3).
_STATION_RE = re.compile(r"^[A-Z0-9]{3,4}$")


def _station_schema(default_station: str = "") -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_STATION_ID, default=default_station): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
            ),
        }
    )


def _reconfigure_schema(default_station: str = "") -> vol.Schema:
    """Schema for the reconfigure step — station ID only."""
    return vol.Schema(
        {
            vol.Required(CONF_STATION_ID, default=default_station): str,
        }
    )


def _options_schema(current_interval: int) -> vol.Schema:
    return vol.Schema(
        {
            vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
            ),
        }
    )


async def _validate_station(hass: HomeAssistant, station_id: str) -> str | None:
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
            if response.status == 204:
                # API returns 204 No Content when the station ID is valid but
                # has no current METAR data (station closed or infrequently reporting).
                return "station_not_found"
            if response.status != 200:
                return "cannot_connect"
            try:
                data = await response.json()
            except (ContentTypeError, ValueError):
                return "cannot_connect"
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

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow the user to change the station ID after initial setup."""
        errors: dict[str, str] = {}
        current_entry = self._get_reconfigure_entry()

        if user_input is not None:
            station_id = user_input[CONF_STATION_ID].strip().upper()
            error = await _validate_station(self.hass, station_id)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(station_id)
                self._abort_if_unique_id_configured()
                return self.async_update_reload_and_abort(
                    current_entry,
                    unique_id=station_id,
                    data_updates={CONF_STATION_ID: station_id},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_reconfigure_schema(
                default_station=current_entry.data.get(CONF_STATION_ID, "")
            ),
            errors=errors,
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            station_id = user_input[CONF_STATION_ID].strip().upper()
            error = await _validate_station(self.hass, station_id)
            if error:
                errors["base"] = error
            else:
                # Prevent duplicate entries for the same station.
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

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the options."""
        current_interval = self.config_entry.data.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        # Options override data when present.
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, current_interval
        )

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(current_interval),
        )
