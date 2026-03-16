"""Tests for the METAR coordinator."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.hametar.coordinator import (
    MetarCoordinator,
    _extract_ceiling,
    _obs_time_to_dt,
    _parse_altimeter_hpa,
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
# _parse_altimeter_hpa unit tests
# ---------------------------------------------------------------------------


def test_parse_altimeter_hpa_a_group():
    """A-group (inHg) is converted to hPa. A3042 = 30.42 inHg = 1030.3 hPa."""
    raw = "METAR KSEA 150553Z VRB06KT 10SM SCT048 05/00 A3042 RMK AO2"
    result = _parse_altimeter_hpa(raw, None)
    assert result == pytest.approx(1030.1, abs=0.1)


def test_parse_altimeter_hpa_q_group():
    """Q-group (hPa) is returned as-is."""
    raw = "METAR EDDB 150550Z AUTO 31008KT 9999 SCT008 05/04 Q1011 TEMPO BKN007"
    result = _parse_altimeter_hpa(raw, None)
    assert result == 1011.0


def test_parse_altimeter_hpa_falls_back_to_api_value():
    """When raw METAR has no altimeter group, fall back to the API value."""
    result = _parse_altimeter_hpa(None, 1013.2)
    assert result == 1013.2


def test_parse_altimeter_hpa_no_raw_no_api():
    """Returns None when both raw METAR and API value are absent."""
    result = _parse_altimeter_hpa(None, None)
    assert result is None


def test_parse_altimeter_hpa_kord_real():
    """KORD real observation: A2987 = 29.87 inHg -> ~1011.8 hPa."""
    raw = "METAR KORD 150551Z 07010KT 10SM OVC075 02/M03 A2987 RMK AO2 SLP122 T00221033 10022 20006 400281022 56040 $"
    result = _parse_altimeter_hpa(raw, 1011.6)
    assert result == pytest.approx(1011.5, abs=0.1)


def test_parse_altimeter_hpa_yssy_real():
    """YSSY real observation: Q1019 -> 1019.0 hPa."""
    raw = "METAR YSSY 150600Z AUTO 03018KT 9999 // NCD 26/16 Q1019"
    result = _parse_altimeter_hpa(raw, 1019)
    assert result == 1019.0


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
# _obs_time_to_dt unit tests
# ---------------------------------------------------------------------------


def test_obs_time_to_dt_valid():
    """Valid Unix epoch returns a UTC-aware datetime."""
    from datetime import datetime, timezone
    result = _obs_time_to_dt(0)
    assert result == datetime(1970, 1, 1, tzinfo=timezone.utc)


def test_obs_time_to_dt_none():
    assert _obs_time_to_dt(None) is None


def test_obs_time_to_dt_invalid_value():
    """Non-numeric string raises ValueError internally and returns None."""
    assert _obs_time_to_dt("not-a-number") is None


def test_obs_time_to_dt_overflow():
    """Extremely large value triggers OverflowError and returns None."""
    assert _obs_time_to_dt(10**18) is None


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
    assert result["altimeter"] == pytest.approx(1013.2)  # hPa as returned by API
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


def test_normalize_altimeter_q_group():
    """Q-group (international) altimeter is returned in hPa unchanged."""
    coord = _make_coordinator()
    raw = {
        "icaoId": "YSSY",
        "wdir": 30,
        "wspd": 18,
        "clouds": [],
        "altim": 1019,
        "rawOb": "METAR YSSY 150600Z AUTO 03018KT 9999 // NCD 26/16 Q1019",
    }
    result = coord._normalize(raw)
    assert result["altimeter"] == 1019.0


def test_normalize_altimeter_a_group():
    """A-group (US) altimeter is converted from inHg to hPa."""
    coord = _make_coordinator()
    raw = {
        "icaoId": "KORD",
        "wdir": 70,
        "wspd": 10,
        "clouds": [],
        "altim": 1011.6,
        "rawOb": "METAR KORD 150551Z 07010KT 10SM OVC075 02/M03 A2987 RMK AO2 SLP122 $",
    }
    result = coord._normalize(raw)
    # A2987 = 29.87 inHg * 33.8639 = 1011.5 hPa
    assert result["altimeter"] == pytest.approx(1011.5, abs=0.1)


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
async def test_update_raises_on_timeout(hass):
    """TimeoutError from aiohttp becomes UpdateFailed."""
    with patch(
        "custom_components.hametar.coordinator.async_get_clientsession"
    ) as mock_session_fn:
        session = MagicMock()
        session.get = MagicMock(side_effect=asyncio.TimeoutError)
        mock_session_fn.return_value = session

        coord = MetarCoordinator(hass, "KORD", 5)
        with pytest.raises(UpdateFailed, match="Timeout"):
            await coord._async_update_data()


@pytest.mark.asyncio
async def test_update_raises_on_http_error_status(hass):
    """ClientResponseError (non-200 HTTP) becomes UpdateFailed with status code."""
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)
    err = aiohttp.ClientResponseError(MagicMock(), MagicMock(), status=503)
    mock_response.raise_for_status = MagicMock(side_effect=err)
    mock_response.json = AsyncMock(return_value=[])

    with patch(
        "custom_components.hametar.coordinator.async_get_clientsession"
    ) as mock_session_fn:
        session = MagicMock()
        session.get = MagicMock(return_value=mock_response)
        mock_session_fn.return_value = session

        coord = MetarCoordinator(hass, "KORD", 5)
        with pytest.raises(UpdateFailed, match="HTTP 503"):
            await coord._async_update_data()


@pytest.mark.asyncio
async def test_update_raises_on_client_error(hass):
    """aiohttp.ClientError becomes UpdateFailed."""
    with patch(
        "custom_components.hametar.coordinator.async_get_clientsession"
    ) as mock_session_fn:
        session = MagicMock()
        session.get = MagicMock(
            side_effect=aiohttp.ClientError("connection refused")
        )
        mock_session_fn.return_value = session

        coord = MetarCoordinator(hass, "KORD", 5)
        with pytest.raises(UpdateFailed, match="Network error"):
            await coord._async_update_data()


@pytest.mark.asyncio
async def test_update_raises_when_empty_response(hass, sample_metar):
    """Empty API response list becomes UpdateFailed."""
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value=[])
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "custom_components.hametar.coordinator.async_get_clientsession"
    ) as mock_session_fn:
        session = MagicMock()
        session.get = MagicMock(return_value=mock_response)
        mock_session_fn.return_value = session

        coord = MetarCoordinator(hass, "KORD", 5)
        with pytest.raises(UpdateFailed, match="No METAR data"):
            await coord._async_update_data()


@pytest.mark.asyncio
async def test_update_success(hass, sample_metar):
    """Successful fetch returns a normalized dict."""
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value=sample_metar)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "custom_components.hametar.coordinator.async_get_clientsession"
    ) as mock_session_fn:
        session = MagicMock()
        session.get = MagicMock(return_value=mock_response)
        mock_session_fn.return_value = session

        coord = MetarCoordinator(hass, "KORD", 5)
        result = await coord._async_update_data()

    assert result["station_id"] == "KORD"
    assert result["flight_category"] == "VFR"
