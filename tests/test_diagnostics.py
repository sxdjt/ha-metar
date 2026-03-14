"""Tests for METAR diagnostics."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.metar.const import CONF_STATION_ID
from custom_components.metar.diagnostics import async_get_config_entry_diagnostics


def _make_entry(station_id="KORD", scan_interval=5, options=None, data=None):
    entry = MagicMock()
    entry.data = data or {CONF_STATION_ID: station_id, "scan_interval": scan_interval}
    entry.options = options or {}
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "station_id": station_id,
        "flight_category": "VFR",
        "temperature": 18.3,
    }
    entry.runtime_data = coordinator
    return entry


@pytest.mark.asyncio
async def test_diagnostics_returns_config_and_data():
    """Diagnostics includes config entry details and coordinator snapshot."""
    hass = MagicMock()
    entry = _make_entry()

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["config_entry"][CONF_STATION_ID] == "KORD"
    assert result["config_entry"]["scan_interval"] == 5
    assert result["last_update_success"] is True
    assert result["coordinator_data"]["flight_category"] == "VFR"


@pytest.mark.asyncio
async def test_diagnostics_uses_options_scan_interval():
    """Options scan_interval is preferred over data scan_interval."""
    hass = MagicMock()
    entry = _make_entry(scan_interval=5, options={"scan_interval": 15})

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["config_entry"]["scan_interval"] == 15


@pytest.mark.asyncio
async def test_diagnostics_when_coordinator_data_none():
    """Diagnostics handles None coordinator data gracefully."""
    hass = MagicMock()
    entry = _make_entry()
    entry.runtime_data.data = None
    entry.runtime_data.last_update_success = False

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["last_update_success"] is False
    assert result["coordinator_data"] is None
