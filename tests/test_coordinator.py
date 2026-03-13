"""Tests for the METAR coordinator."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.metar.coordinator import (
    MetarCoordinator,
    _extract_ceiling,
    _parse_visibility,
)
from homeassistant.helpers.update_coordinator import UpdateFailed


# ---------------------------------------------------------------------------
# _parse_visibility unit tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("10+", 10.0),
        ("10", 10.0),
        (10, 10.0),
        ("6", 6.0),
        ("1/2", 0.5),
        ("1/4", 0.25),
        ("1 1/2", 1.5),
        ("1 3/4", 1.75),
        ("P6SM", None),    # unrecognized prefix: can't parse
        (None, None),
        ("", None),
    ],
)
def test_parse_visibility(raw, expected):
    result = _parse_visibility(raw)
    if expected is None:
        assert result is None
    else:
        assert result == pytest.approx(expected)


# ---------------------------------------------------------------------------
# _extract_ceiling unit tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "clouds, expected",
    [
        # Clear sky
        ([], None),
        (None, None),
        # Only FEW — not a ceiling
        ([{"cover": "FEW", "base": 5000}], None),
        # Single BKN layer
        ([{"cover": "BKN", "base": 3000}], 3000),
        # OVC layer
        ([{"cover": "OVC", "base": 800}], 800),
        # VV (vertical visibility) counts as ceiling
        ([{"cover": "VV", "base": 200}], 200),
        # Multiple layers — return the lowest ceiling
        (
            [
                {"cover": "FEW", "base": 2000},
                {"cover": "SCT", "base": 4000},
                {"cover": "BKN", "base": 6000},
                {"cover": "OVC", "base": 1500},
            ],
            1500,
        ),
        # Layer with no base height
        ([{"cover": "OVC", "base": None}], None),
    ],
)
def test_extract_ceiling(clouds, expected):
    assert _extract_ceiling(clouds) == expected


# ---------------------------------------------------------------------------
# MetarCoordinator._normalize
# ---------------------------------------------------------------------------


def _make_coordinator(hass=None):
    """Build a MetarCoordinator with a minimal hass mock."""
    if hass is None:
        hass = MagicMock()
    coord = MetarCoordinator.__new__(MetarCoordinator)
    coord.station_id = "KORD"
    coord.hass = hass
    coord.logger = MagicMock()
    return coord


def test_normalize_standard(sample_metar):
    """Standard VFR observation normalizes correctly."""
    coord = _make_coordinator()
    result = coord._normalize(sample_metar[0])

    assert result["station_id"] == "KORD"
    assert result["station_name"] == "Chicago O Hare Intl"
    assert result["flight_category"] == "VFR"
    assert result["temperature"] == pytest.approx(18.3)
    assert result["dewpoint"] == pytest.approx(6.1)
    assert result["wind_direction"] == 270
    assert result["wind_variable"] is False
    assert result["wind_speed"] == 12
    assert result["wind_gust"] == 18
    assert result["visibility"] == pytest.approx(10.0)
    assert result["altimeter"] == pytest.approx(29.92)
    assert result["ceiling"] is None          # FEW layer is not a ceiling
    assert result["wx_string"] is None        # empty string becomes None
    assert "KORD" in result["raw_metar"]


def test_normalize_lifr(sample_metar_ifr):
    """LIFR observation: ceiling and fractional visibility are extracted."""
    coord = _make_coordinator()
    result = coord._normalize(sample_metar_ifr[0])

    assert result["flight_category"] == "LIFR"
    assert result["visibility"] == pytest.approx(0.5)
    assert result["ceiling"] == 500
    assert result["wx_string"] == "-RA BR"
    assert result["wind_gust"] is None


def test_normalize_variable_wind():
    """Variable wind direction maps to None with wind_variable=True."""
    coord = _make_coordinator()
    raw = {
        "icaoId": "KORD",
        "wdir": "VRB",
        "wspd": 3,
        "wgst": None,
        "clouds": [],
    }
    result = coord._normalize(raw)
    assert result["wind_direction"] is None
    assert result["wind_variable"] is True


# ---------------------------------------------------------------------------
# MetarCoordinator._async_update_data — HTTP error paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_raises_on_timeout(hass_mock):
    """TimeoutError from aiohttp becomes UpdateFailed."""
    with patch(
        "custom_components.metar.coordinator.async_get_clientsession"
    ) as mock_session_fn:
        session = MagicMock()
        session.get = MagicMock(side_effect=asyncio.TimeoutError)
        mock_session_fn.return_value = session

        coord = MetarCoordinator(hass_mock, "KORD", 5)
        with pytest.raises(UpdateFailed, match="Timeout"):
            await coord._async_update_data()


@pytest.mark.asyncio
async def test_update_raises_on_client_error(hass_mock):
    """aiohttp.ClientError becomes UpdateFailed."""
    with patch(
        "custom_components.metar.coordinator.async_get_clientsession"
    ) as mock_session_fn:
        session = MagicMock()
        session.get = MagicMock(
            side_effect=aiohttp.ClientError("connection refused")
        )
        mock_session_fn.return_value = session

        coord = MetarCoordinator(hass_mock, "KORD", 5)
        with pytest.raises(UpdateFailed, match="Network error"):
            await coord._async_update_data()


@pytest.mark.asyncio
async def test_update_raises_when_empty_response(hass_mock, sample_metar):
    """Empty API response list becomes UpdateFailed."""
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value=[])
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "custom_components.metar.coordinator.async_get_clientsession"
    ) as mock_session_fn:
        session = MagicMock()
        session.get = MagicMock(return_value=mock_response)
        mock_session_fn.return_value = session

        coord = MetarCoordinator(hass_mock, "KORD", 5)
        with pytest.raises(UpdateFailed, match="No METAR data"):
            await coord._async_update_data()


@pytest.mark.asyncio
async def test_update_success(hass_mock, sample_metar):
    """Successful fetch returns a normalized dict."""
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value=sample_metar)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "custom_components.metar.coordinator.async_get_clientsession"
    ) as mock_session_fn:
        session = MagicMock()
        session.get = MagicMock(return_value=mock_response)
        mock_session_fn.return_value = session

        coord = MetarCoordinator(hass_mock, "KORD", 5)
        result = await coord._async_update_data()

    assert result["station_id"] == "KORD"
    assert result["flight_category"] == "VFR"


# ---------------------------------------------------------------------------
# Fixture: minimal hass mock (avoids pulling in pytest-homeassistant-custom-component
# just for coordinator tests that don't need full HA machinery)
# ---------------------------------------------------------------------------


@pytest.fixture
def hass_mock():
    """Return a minimal hass mock sufficient for coordinator instantiation."""
    hass = MagicMock()
    hass.loop = asyncio.get_event_loop()
    return hass
