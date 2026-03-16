"""Diagnostics for the METAR integration."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import MetarConfigEntry
from .const import CONF_STATION_ID


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: MetarConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a METAR config entry."""
    coordinator = entry.runtime_data
    return {
        "config_entry": {
            CONF_STATION_ID: entry.data[CONF_STATION_ID],
            "scan_interval": entry.options.get("scan_interval")
            or entry.data.get("scan_interval"),
        },
        "last_update_success": coordinator.last_update_success,
        "coordinator_data": coordinator.data,
    }
