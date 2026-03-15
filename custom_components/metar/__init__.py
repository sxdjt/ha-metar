"""The METAR integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant

from homeassistant.helpers import entity_registry as er

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

    # Migrate entity IDs from the old {station}_{key} format to metar_{station}_{key}.
    # This runs before platform setup so the registry reflects the new IDs when
    # entities are loaded.
    _migrate_entity_ids(hass, entry, station_id)

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


def _migrate_entity_ids(
    hass: HomeAssistant, entry: MetarConfigEntry, station_id: str
) -> None:
    """Rename entity IDs from sensor.{station}_{key} to sensor.metar_{station}_{key}."""
    station_lower = station_id.lower()
    old_prefix = f"sensor.{station_lower}_"
    new_prefix = f"sensor.metar_{station_lower}_"
    entity_reg = er.async_get(hass)

    for reg_entry in er.async_entries_for_config_entry(entity_reg, entry.entry_id):
        if reg_entry.entity_id.startswith(old_prefix) and not reg_entry.entity_id.startswith(new_prefix):
            new_entity_id = new_prefix + reg_entry.entity_id[len(old_prefix):]
            entity_reg.async_update_entity(reg_entry.entity_id, new_entity_id=new_entity_id)
            _LOGGER.debug("Migrated entity ID %s -> %s", reg_entry.entity_id, new_entity_id)


async def _async_update_listener(hass: HomeAssistant, entry: MetarConfigEntry) -> None:
    """Reload the entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
