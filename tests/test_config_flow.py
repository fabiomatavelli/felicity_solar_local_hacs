"""Tests for the Felicity Solar Local config and options flows."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.felicity_solar_local.api import (
    FelicityConnectionError,
    FelicityProtocolError,
    FelicityTimeoutError,
)
from custom_components.felicity_solar_local.const import (
    CONF_HOST,
    CONF_PERSISTENT_CONNECTION,
    CONF_PORT,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)

pytestmark = pytest.mark.asyncio

API_PATH = "custom_components.felicity_solar_local.config_flow.FelicityLocalClient.async_get_data"


async def test_user_flow_success(
    hass: HomeAssistant, sample_response: dict[str, Any]
) -> None:
    with patch(API_PATH, AsyncMock(return_value=sample_response)):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "192.168.1.50", CONF_PORT: 53970}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: "192.168.1.50", CONF_PORT: 53970}
    assert sample_response["DevSN"] in result["title"]


@pytest.mark.parametrize(
    ("exception", "expected_error"),
    [
        (FelicityConnectionError("boom"), "cannot_connect"),
        (FelicityTimeoutError("boom"), "timeout"),
        (FelicityProtocolError("boom"), "invalid_response"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant, exception: Exception, expected_error: str
) -> None:
    with patch(API_PATH, AsyncMock(side_effect=exception)):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "192.168.1.50", CONF_PORT: 53970}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}


async def test_user_flow_aborts_on_duplicate(
    hass: HomeAssistant, sample_response: dict[str, Any]
) -> None:
    existing = MockConfigEntry(
        domain=DOMAIN,
        unique_id=sample_response["DevSN"],
        data={CONF_HOST: "192.168.1.50", CONF_PORT: 53970},
    )
    existing.add_to_hass(hass)

    with patch(API_PATH, AsyncMock(return_value=sample_response)):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "192.168.1.50", CONF_PORT: 53970}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow_updates_interval(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="test-serial",
        data={CONF_HOST: "192.168.1.50", CONF_PORT: 53970},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_UPDATE_INTERVAL: 60, CONF_PERSISTENT_CONNECTION: False},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_UPDATE_INTERVAL: 60,
        CONF_PERSISTENT_CONNECTION: False,
    }


async def test_options_flow_rejects_low_interval_in_one_shot_mode(
    hass: HomeAssistant,
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="test-serial",
        data={CONF_HOST: "192.168.1.50", CONF_PORT: 53970},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_UPDATE_INTERVAL: 5, CONF_PERSISTENT_CONNECTION: False},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "interval_too_low_for_one_shot"}


async def test_options_flow_allows_low_interval_when_persistent(
    hass: HomeAssistant,
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="test-serial",
        data={CONF_HOST: "192.168.1.50", CONF_PORT: 53970},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_UPDATE_INTERVAL: 5, CONF_PERSISTENT_CONNECTION: True},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_UPDATE_INTERVAL: 5,
        CONF_PERSISTENT_CONNECTION: True,
    }
