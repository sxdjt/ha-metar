"""Tests for the METAR config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.metar.config_flow import (
    MetarConfigFlow,
    MetarOptionsFlow,
    _reconfigure_schema,
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
    assert await _validate_station(hass, "K") == "invalid_station_format"
    assert await _validate_station(hass, "KORDXX") == "invalid_station_format"
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
async def test_validate_station_non_list_response():
    """Non-list API response returns station_not_found."""
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"error": "bad"})

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)

    hass = MagicMock()
    with patch(
        "custom_components.metar.config_flow.async_get_clientsession",
        return_value=mock_session,
    ):
        assert await _validate_station(hass, "KORD") == "station_not_found"


@pytest.mark.asyncio
async def test_validate_station_http_error():
    """Non-200/204 HTTP status returns cannot_connect."""
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
async def test_validate_station_204_no_content():
    """HTTP 204 (station known but no current data) returns station_not_found."""
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)
    mock_response.status = 204

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)

    hass = MagicMock()
    with patch(
        "custom_components.metar.config_flow.async_get_clientsession",
        return_value=mock_session,
    ):
        assert await _validate_station(hass, "XXXX") == "station_not_found"


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


@pytest.mark.asyncio
async def test_validate_station_strips_and_uppercases():
    """Whitespace and lowercase are normalized before checking format."""
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=[{"icaoId": "KORD"}])

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)

    hass = MagicMock()
    with patch(
        "custom_components.metar.config_flow.async_get_clientsession",
        return_value=mock_session,
    ):
        # " kord " should normalize to "KORD" and pass
        result = await _validate_station(hass, " kord ")
    assert result is None


# ---------------------------------------------------------------------------
# MetarConfigFlow.async_step_user
# ---------------------------------------------------------------------------


def _build_config_flow(hass):
    """Return a MetarConfigFlow with hass and standard mock helpers."""
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
async def test_step_user_shows_form_on_first_call():
    """With no user_input, the form is returned."""
    flow = _build_config_flow(MagicMock())
    result = await flow.async_step_user(user_input=None)
    assert result["type"] == "form"
    flow.async_show_form.assert_called_once()


@pytest.mark.asyncio
async def test_step_user_creates_entry_on_valid_input():
    """Valid station creates a config entry."""
    flow = _build_config_flow(MagicMock())

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
    flow = _build_config_flow(MagicMock())

    with patch(
        "custom_components.metar.config_flow._validate_station",
        new=AsyncMock(return_value="station_not_found"),
    ):
        result = await flow.async_step_user(
            user_input={CONF_STATION_ID: "ZZZZ", "scan_interval": 5}
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "station_not_found"}


@pytest.mark.asyncio
async def test_step_user_abort_on_duplicate():
    """Duplicate station ID aborts the flow."""
    flow = _build_config_flow(MagicMock())
    flow._abort_if_unique_id_configured = MagicMock(side_effect=Exception("already configured"))

    with patch(
        "custom_components.metar.config_flow._validate_station",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(Exception, match="already configured"):
            await flow.async_step_user(
                user_input={CONF_STATION_ID: "KORD", "scan_interval": 5}
            )


@pytest.mark.asyncio
async def test_step_user_shows_form_on_cannot_connect():
    """Cannot-connect validation error shows form with error."""
    flow = _build_config_flow(MagicMock())

    with patch(
        "custom_components.metar.config_flow._validate_station",
        new=AsyncMock(return_value="cannot_connect"),
    ):
        result = await flow.async_step_user(
            user_input={CONF_STATION_ID: "KORD", "scan_interval": 5}
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "cannot_connect"}


# ---------------------------------------------------------------------------
# MetarConfigFlow.async_get_options_flow
# ---------------------------------------------------------------------------


def test_async_get_options_flow():
    """async_get_options_flow returns a MetarOptionsFlow instance."""
    config_entry = MagicMock()
    flow = MetarConfigFlow.async_get_options_flow(config_entry)
    assert isinstance(flow, MetarOptionsFlow)


# ---------------------------------------------------------------------------
# MetarConfigFlow.async_step_reconfigure
# ---------------------------------------------------------------------------


class _ReconfigureFlow(MetarConfigFlow):
    """Test subclass that injects a current config entry for reconfigure."""

    def __init__(self, entry):
        self._injected_entry = entry

    def _get_reconfigure_entry(self):
        return self._injected_entry


def _build_reconfigure_flow(current_station="KORD"):
    entry = MagicMock()
    entry.data = {"station_id": current_station}
    flow = _ReconfigureFlow(entry)
    flow.hass = MagicMock()
    flow.context = {"source": "reconfigure"}
    flow._abort_if_unique_id_configured = MagicMock()
    flow.async_set_unique_id = AsyncMock()
    flow.async_show_form = MagicMock(
        side_effect=lambda **kwargs: {"type": "form", **kwargs}
    )
    flow.async_update_reload_and_abort = MagicMock(
        side_effect=lambda entry, unique_id=None, data_updates=None: {
            "type": "abort",
            "reason": "reconfigure_successful",
            "unique_id": unique_id,
            "data_updates": data_updates,
        }
    )
    return flow


@pytest.mark.asyncio
async def test_reconfigure_shows_form_with_current_station():
    """Reconfigure form is pre-filled with the current station ID."""
    flow = _build_reconfigure_flow(current_station="KORD")
    result = await flow.async_step_reconfigure(user_input=None)
    assert result["type"] == "form"
    assert result["step_id"] == "reconfigure"


@pytest.mark.asyncio
async def test_reconfigure_success():
    """Valid new station updates the entry and reloads."""
    flow = _build_reconfigure_flow(current_station="KORD")

    with patch(
        "custom_components.metar.config_flow._validate_station",
        new=AsyncMock(return_value=None),
    ):
        result = await flow.async_step_reconfigure(
            user_input={"station_id": "egll"}
        )

    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"
    assert result["unique_id"] == "EGLL"
    assert result["data_updates"] == {"station_id": "EGLL"}


@pytest.mark.asyncio
async def test_reconfigure_shows_error_on_invalid_station():
    """Invalid station re-shows the form with an error."""
    flow = _build_reconfigure_flow()

    with patch(
        "custom_components.metar.config_flow._validate_station",
        new=AsyncMock(return_value="station_not_found"),
    ):
        result = await flow.async_step_reconfigure(
            user_input={"station_id": "ZZZZ"}
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "station_not_found"}


@pytest.mark.asyncio
async def test_reconfigure_aborts_on_duplicate():
    """Reconfiguring to an already-configured station aborts."""
    flow = _build_reconfigure_flow()
    flow._abort_if_unique_id_configured = MagicMock(
        side_effect=Exception("already configured")
    )

    with patch(
        "custom_components.metar.config_flow._validate_station",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(Exception, match="already configured"):
            await flow.async_step_reconfigure(user_input={"station_id": "EGLL"})


def test_reconfigure_schema_station_only():
    """Reconfigure schema contains only station_id, not scan_interval."""
    schema = _reconfigure_schema("KORD")
    keys = [str(k) for k in schema.schema.keys()]
    assert "station_id" in keys
    assert "scan_interval" not in keys


# ---------------------------------------------------------------------------
# MetarOptionsFlow.async_step_init
# ---------------------------------------------------------------------------


class _OptionsFlowWithEntry(MetarOptionsFlow):
    """Test subclass that injects a config_entry via property."""

    def __init__(self, entry):
        self._injected_entry = entry

    @property
    def config_entry(self):
        return self._injected_entry


def _build_options_flow(data=None, options=None):
    """Return a MetarOptionsFlow backed by a mock config entry."""
    entry = MagicMock()
    entry.data = data or {"scan_interval": DEFAULT_SCAN_INTERVAL}
    entry.options = options or {}
    flow = _OptionsFlowWithEntry(entry)
    flow.async_show_form = MagicMock(
        side_effect=lambda **kwargs: {"type": "form", **kwargs}
    )
    flow.async_create_entry = MagicMock(
        side_effect=lambda title, data: {"type": "create_entry", "data": data}
    )
    return flow


@pytest.mark.asyncio
async def test_options_flow_shows_form():
    """Options flow shows current interval on first call."""
    flow = _build_options_flow(data={"scan_interval": 10})
    result = await flow.async_step_init(user_input=None)
    assert result["type"] == "form"


@pytest.mark.asyncio
async def test_options_flow_saves_new_interval():
    """Options flow creates an entry with the new interval."""
    flow = _build_options_flow(data={"scan_interval": 5})
    result = await flow.async_step_init(user_input={"scan_interval": 15})
    assert result["type"] == "create_entry"
    assert result["data"]["scan_interval"] == 15


@pytest.mark.asyncio
async def test_options_flow_uses_options_as_default():
    """Options override data when pre-existing options are set."""
    flow = _build_options_flow(
        data={"scan_interval": 5},
        options={"scan_interval": 20},
    )
    result = await flow.async_step_init(user_input=None)
    assert result["type"] == "form"
    # Verify current_interval was read from options (20), not data (5)
    call_kwargs = flow.async_show_form.call_args.kwargs
    schema = call_kwargs["data_schema"].schema
    # The default value in the schema reflects the current_interval
    for key in schema:
        if hasattr(key, "default") and str(key) == "scan_interval":
            assert key.default() == 20
