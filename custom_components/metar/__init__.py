"""The METAR integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant

from .const import CONF_STATION_ID, DEFAULT_SCAN_INTERVAL, PLATFORMS
from .coordinator import MetarCoordinator

_LOGGER = logging.getLogger(__name__)

# Typed config entry — gives full type-safety when accessing entry.runtime_data.
type MetarConfigEntry = ConfigEntry[MetarCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: MetarConfigEntry) -> bool:
    """Set up METAR from a config entry."""
    station_id = entry.data[CONF_STATION_ID]

    # Options take precedence over initial data for the poll interval.
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    coordinator = MetarCoordinator(hass, station_id, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload the entry when options change (e.g. poll interval).
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: MetarConfigEntry) -> bool:
    """Unload a METAR config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: MetarConfigEntry) -> None:
    """Reload the entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
