"""Shared pytest fixtures for METAR integration tests."""

import pytest

# ---------------------------------------------------------------------------
# Sample API response — mirrors the real AWC JSON payload for one station.
# ---------------------------------------------------------------------------

SAMPLE_METAR_RESPONSE = [
    {
        "metar_id": 1234567,
        "icaoId": "KORD",
        "receiveTime": "2024-03-13 19:55:00",
        "reportTime": "2024-03-13 19:52:00",
        "temp": 18.3,
        "dewp": 6.1,
        "wdir": 270,
        "wspd": 12,
        "wgst": 18,
        "visib": "10+",
        "altim": 1013.2,
        "slp": 1013.2,
        "wxString": "",
        "metarType": "METAR",
        "rawOb": "KORD 131952Z 27012G18KT 10SM FEW050 18/06 A2992 RMK AO2",
        "mostRecent": 1,
        "lat": 41.98,
        "lon": -87.91,
        "elev": 205,
        "name": "Chicago O Hare Intl",
        "clouds": [{"cover": "FEW", "base": 5000}],
        "fltCat": "VFR",
    }
]

SAMPLE_METAR_IFR = [
    {
        "icaoId": "KORD",
        "reportTime": "2024-03-13 20:00:00",
        "temp": 10.0,
        "dewp": 9.0,
        "wdir": 180,
        "wspd": 5,
        "wgst": None,
        "visib": "1/2",
        "altim": 998.8,
        "wxString": "-RA BR",
        "rawOb": "KORD 132000Z 18005KT 1/2SM -RA BR OVC005 10/09 A2950",
        "name": "Chicago O Hare Intl",
        "clouds": [
            {"cover": "OVC", "base": 500},
        ],
        "fltCat": "LIFR",
    }
]


@pytest.fixture
def sample_metar():
    """Return a standard VFR METAR API response."""
    return SAMPLE_METAR_RESPONSE


@pytest.fixture
def sample_metar_ifr():
    """Return a LIFR METAR API response for edge-case testing."""
    return SAMPLE_METAR_IFR
