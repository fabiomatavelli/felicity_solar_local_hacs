"""Tests for FelicityLocalCoordinator."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.felicity_solar_local.api import FelicityConnectionError
from custom_components.felicity_solar_local.const import CONF_HOST, CONF_PORT, DOMAIN
from custom_components.felicity_solar_local.coordinator import FelicityLocalCoordinator
from custom_components.felicity_solar_local.profiles import FLB48314TG1H_PROFILE

pytestmark = pytest.mark.asyncio

API_PATH = "custom_components.felicity_solar_local.coordinator.FelicityLocalClient.async_get_data"


def _make_coordinator(
    hass: HomeAssistant, persistent_connection: bool = False
) -> FelicityLocalCoordinator:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="test-serial",
        data={CONF_HOST: "192.168.1.50", CONF_PORT: 53970},
    )
    entry.add_to_hass(hass)
    return FelicityLocalCoordinator(
        hass=hass,
        config_entry=entry,
        host="192.168.1.50",
        port=53970,
        update_interval=30,
        persistent_connection=persistent_connection,
    )


async def test_update_data_selects_profile_and_parses(
    hass: HomeAssistant, sample_response: dict[str, Any]
) -> None:
    coordinator = _make_coordinator(hass)

    with patch(API_PATH, AsyncMock(return_value=sample_response)):
        result = await coordinator._async_update_data()

    assert result.raw == sample_response
    assert result.profile is FLB48314TG1H_PROFILE
    assert result.data["voltage"] == 54.04


async def test_update_data_raises_update_failed_on_client_error(
    hass: HomeAssistant,
) -> None:
    coordinator = _make_coordinator(hass)

    with (
        patch(API_PATH, AsyncMock(side_effect=FelicityConnectionError("boom"))),
        pytest.raises(UpdateFailed),
    ):
        await coordinator._async_update_data()


async def test_persistent_connection_flag_passed_to_client(hass: HomeAssistant) -> None:
    assert _make_coordinator(hass, persistent_connection=False).client.persistent is False
    assert _make_coordinator(hass, persistent_connection=True).client.persistent is True
