"""Tests for the METAR integration setup and teardown."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.hametar import (
    MetarConfigEntry,
    _async_update_listener,
    _migrate_entity_ids,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.hametar.const import CONF_STATION_ID, DEFAULT_SCAN_INTERVAL


def _make_entry(data=None, options=None):
    """Return a mock config entry."""
    entry = MagicMock()
    entry.data = data or {CONF_STATION_ID: "KORD", "scan_interval": 5}
    entry.options = options or {}
    entry.async_on_unload = MagicMock()
    return entry


def _make_hass():
    """Return a minimal hass mock."""
    hass = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=None)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.config_entries.async_reload = AsyncMock(return_value=None)
    return hass


# ---------------------------------------------------------------------------
# async_setup_entry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_setup_entry_stores_coordinator_in_runtime_data():
    """Coordinator is stored in entry.runtime_data after setup."""
    hass = _make_hass()
    entry = _make_entry()

    mock_coordinator = MagicMock()
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch("custom_components.hametar.MetarCoordinator", return_value=mock_coordinator):
        result = await async_setup_entry(hass, entry)

    assert result is True
    assert entry.runtime_data is mock_coordinator


@pytest.mark.asyncio
async def test_setup_entry_calls_first_refresh():
    """async_config_entry_first_refresh is called during setup."""
    hass = _make_hass()
    entry = _make_entry()

    mock_coordinator = MagicMock()
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch("custom_components.hametar.MetarCoordinator", return_value=mock_coordinator):
        await async_setup_entry(hass, entry)

    mock_coordinator.async_config_entry_first_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_setup_entry_forwards_to_sensor_platform():
    """async_forward_entry_setups is called with the sensor platform."""
    from custom_components.hametar.const import PLATFORMS

    hass = _make_hass()
    entry = _make_entry()

    mock_coordinator = MagicMock()
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch("custom_components.hametar.MetarCoordinator", return_value=mock_coordinator):
        await async_setup_entry(hass, entry)

    hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(entry, PLATFORMS)


@pytest.mark.asyncio
async def test_setup_entry_uses_data_scan_interval():
    """Scan interval is read from entry.data when options are absent."""
    hass = _make_hass()
    entry = _make_entry(data={CONF_STATION_ID: "KORD", "scan_interval": 10})

    mock_coordinator = MagicMock()
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch("custom_components.hametar.MetarCoordinator", return_value=mock_coordinator) as cls:
        await async_setup_entry(hass, entry)

    # Third positional arg to MetarCoordinator is scan_interval
    _, args, _ = cls.mock_calls[0]
    assert args[2] == 10


@pytest.mark.asyncio
async def test_setup_entry_options_override_data_scan_interval():
    """Options scan_interval takes precedence over data scan_interval."""
    hass = _make_hass()
    entry = _make_entry(
        data={CONF_STATION_ID: "KORD", "scan_interval": 5},
        options={"scan_interval": 20},
    )

    mock_coordinator = MagicMock()
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch("custom_components.hametar.MetarCoordinator", return_value=mock_coordinator) as cls:
        await async_setup_entry(hass, entry)

    _, args, _ = cls.mock_calls[0]
    assert args[2] == 20


@pytest.mark.asyncio
async def test_setup_entry_uses_default_scan_interval_when_absent():
    """DEFAULT_SCAN_INTERVAL is used when no interval is in data or options."""
    hass = _make_hass()
    entry = _make_entry(data={CONF_STATION_ID: "KORD"})  # no scan_interval key

    mock_coordinator = MagicMock()
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch("custom_components.hametar.MetarCoordinator", return_value=mock_coordinator) as cls:
        await async_setup_entry(hass, entry)

    _, args, _ = cls.mock_calls[0]
    assert args[2] == DEFAULT_SCAN_INTERVAL


@pytest.mark.asyncio
async def test_setup_entry_registers_options_listener():
    """An options-change listener is registered during setup."""
    hass = _make_hass()
    entry = _make_entry()

    mock_coordinator = MagicMock()
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch("custom_components.hametar.MetarCoordinator", return_value=mock_coordinator):
        await async_setup_entry(hass, entry)

    entry.async_on_unload.assert_called_once()


# ---------------------------------------------------------------------------
# async_unload_entry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unload_entry_returns_true_on_success():
    """async_unload_entry returns True when platform unload succeeds."""
    hass = _make_hass()
    entry = _make_entry()

    result = await async_unload_entry(hass, entry)

    assert result is True


@pytest.mark.asyncio
async def test_unload_entry_calls_unload_platforms():
    """async_unload_entry delegates to async_unload_platforms."""
    from custom_components.hametar.const import PLATFORMS

    hass = _make_hass()
    entry = _make_entry()

    await async_unload_entry(hass, entry)

    hass.config_entries.async_unload_platforms.assert_awaited_once_with(entry, PLATFORMS)


@pytest.mark.asyncio
async def test_unload_entry_returns_false_when_platform_unload_fails():
    """async_unload_entry propagates False from async_unload_platforms."""
    hass = _make_hass()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)
    entry = _make_entry()

    result = await async_unload_entry(hass, entry)

    assert result is False


# ---------------------------------------------------------------------------
# _async_update_listener
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _migrate_entity_ids
# ---------------------------------------------------------------------------


def test_migrate_entity_ids_renames_old_format():
    """Entities with the old {station}_{key} format are renamed."""
    hass = MagicMock()
    entry = _make_entry()
    entry.entry_id = "test_entry_id"

    old_entity = MagicMock()
    old_entity.entity_id = "sensor.kord_altimeter"

    mock_registry = MagicMock()

    with (
        patch("custom_components.hametar.er.async_get", return_value=mock_registry),
        patch(
            "custom_components.hametar.er.async_entries_for_config_entry",
            return_value=[old_entity],
        ),
    ):
        _migrate_entity_ids(hass, entry, "KORD")

    mock_registry.async_update_entity.assert_called_once_with(
        "sensor.kord_altimeter", new_entity_id="sensor.metar_kord_altimeter"
    )


def test_migrate_entity_ids_skips_already_migrated():
    """Entities already in metar_{station}_{key} format are left untouched."""
    hass = MagicMock()
    entry = _make_entry()
    entry.entry_id = "test_entry_id"

    new_entity = MagicMock()
    new_entity.entity_id = "sensor.metar_kord_altimeter"

    mock_registry = MagicMock()

    with (
        patch("custom_components.hametar.er.async_get", return_value=mock_registry),
        patch(
            "custom_components.hametar.er.async_entries_for_config_entry",
            return_value=[new_entity],
        ),
    ):
        _migrate_entity_ids(hass, entry, "KORD")

    mock_registry.async_update_entity.assert_not_called()


@pytest.mark.asyncio
async def test_update_listener_reloads_entry():
    """Options listener triggers a config entry reload."""
    hass = _make_hass()
    entry = _make_entry()

    await _async_update_listener(hass, entry)

    hass.config_entries.async_reload.assert_awaited_once_with(entry.entry_id)
