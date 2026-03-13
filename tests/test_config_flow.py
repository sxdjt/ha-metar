"""Tests for the METAR config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.metar.config_flow import (
    MetarConfigFlow,
    MetarOptionsFlow,
    _validate_station,
)
from custom_components.metar.const import CONF_STATION_ID, DEFAULT_SCAN_INTERVAL


# ---------------------------------------------------------------------------
# _validate_station helper
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_station_bad_format():
    """Station IDs that don't match the ICAO pattern are rejected immediately."""
    hass = MagicMock()
    # Too short
    assert await _validate_station(hass, "K") == "invalid_station_format"
    # Too long
    assert await _validate_station(hass, "KORDXX") == "invalid_station_format"
    # Contains invalid characters
    assert await _validate_station(hass, "K@RD") == "invalid_station_format"


@pytest.mark.asyncio
async def test_validate_station_cannot_connect():
    """Network error during validation returns cannot_connect."""
    import aiohttp

    mock_session = MagicMock()
    mock_session.get = MagicMock(side_effect=aiohttp.ClientError("down"))

    hass = MagicMock()
    with patch(
        "custom_components.metar.config_flow.async_get_clientsession",
        return_value=mock_session,
    ):
        assert await _validate_station(hass, "KORD") == "cannot_connect"


@pytest.mark.asyncio
async def test_validate_station_not_found():
    """Empty API response returns station_not_found."""
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=[])

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)

    hass = MagicMock()
    with patch(
        "custom_components.metar.config_flow.async_get_clientsession",
        return_value=mock_session,
    ):
        assert await _validate_station(hass, "ZZZZ") == "station_not_found"


@pytest.mark.asyncio
async def test_validate_station_http_error():
    """Non-200 HTTP status returns cannot_connect."""
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)
    mock_response.status = 503

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)

    hass = MagicMock()
    with patch(
        "custom_components.metar.config_flow.async_get_clientsession",
        return_value=mock_session,
    ):
        assert await _validate_station(hass, "KORD") == "cannot_connect"


@pytest.mark.asyncio
async def test_validate_station_success(sample_metar):
    """Valid station with data returns None (no error)."""
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=sample_metar)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)

    hass = MagicMock()
    with patch(
        "custom_components.metar.config_flow.async_get_clientsession",
        return_value=mock_session,
    ):
        assert await _validate_station(hass, "KORD") is None


# ---------------------------------------------------------------------------
# MetarConfigFlow.async_step_user
# ---------------------------------------------------------------------------


def _build_config_flow(hass, sample_metar):
    """Return a MetarConfigFlow with hass and a patched validator."""
    flow = MetarConfigFlow()
    flow.hass = hass
    flow.context = {"source": "user"}
    flow._abort_if_unique_id_configured = MagicMock()
    flow.async_set_unique_id = AsyncMock()
    flow.async_create_entry = MagicMock(
        side_effect=lambda title, data: {"type": "create_entry", "title": title, "data": data}
    )
    flow.async_show_form = MagicMock(
        side_effect=lambda **kwargs: {"type": "form", **kwargs}
    )
    return flow


@pytest.mark.asyncio
async def test_step_user_shows_form_on_first_call(sample_metar):
    """With no user_input, the form is returned."""
    hass = MagicMock()
    flow = _build_config_flow(hass, sample_metar)
    result = await flow.async_step_user(user_input=None)
    assert result["type"] == "form"
    flow.async_show_form.assert_called_once()


@pytest.mark.asyncio
async def test_step_user_creates_entry_on_valid_input(sample_metar):
    """Valid station creates a config entry."""
    hass = MagicMock()
    flow = _build_config_flow(hass, sample_metar)

    with patch(
        "custom_components.metar.config_flow._validate_station",
        new=AsyncMock(return_value=None),
    ):
        result = await flow.async_step_user(
            user_input={CONF_STATION_ID: "kord", "scan_interval": 5}
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "KORD"
    assert result["data"][CONF_STATION_ID] == "KORD"
    assert result["data"]["scan_interval"] == 5


@pytest.mark.asyncio
async def test_step_user_shows_error_on_invalid_station():
    """Validation failure re-shows the form with an error."""
    hass = MagicMock()
    flow = MetarConfigFlow()
    flow.hass = hass
    flow.context = {"source": "user"}
    flow.async_show_form = MagicMock(
        side_effect=lambda **kwargs: {"type": "form", **kwargs}
    )

    with patch(
        "custom_components.metar.config_flow._validate_station",
        new=AsyncMock(return_value="station_not_found"),
    ):
        result = await flow.async_step_user(
            user_input={CONF_STATION_ID: "ZZZZ", "scan_interval": 5}
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "station_not_found"}


# ---------------------------------------------------------------------------
# MetarOptionsFlow.async_step_init
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_options_flow_shows_form():
    """Options flow shows current interval on first call."""
    config_entry = MagicMock()
    config_entry.data = {"scan_interval": 10}
    config_entry.options = {}

    flow = MetarOptionsFlow()
    flow.config_entry = config_entry
    flow.async_show_form = MagicMock(
        side_effect=lambda **kwargs: {"type": "form", **kwargs}
    )
    flow.async_create_entry = MagicMock(
        side_effect=lambda title, data: {"type": "create_entry", "data": data}
    )

    result = await flow.async_step_init(user_input=None)
    assert result["type"] == "form"


@pytest.mark.asyncio
async def test_options_flow_saves_new_interval():
    """Options flow creates an entry with the new interval."""
    config_entry = MagicMock()
    config_entry.data = {"scan_interval": 5}
    config_entry.options = {}

    flow = MetarOptionsFlow()
    flow.config_entry = config_entry
    flow.async_create_entry = MagicMock(
        side_effect=lambda title, data: {"type": "create_entry", "data": data}
    )

    result = await flow.async_step_init(user_input={"scan_interval": 15})
    assert result["type"] == "create_entry"
    assert result["data"]["scan_interval"] == 15
