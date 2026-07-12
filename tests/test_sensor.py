"""End-to-end test: config entry setup produces the expected sensor entities."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.felicity_solar_local.const import CONF_HOST, CONF_PORT, DOMAIN

pytestmark = pytest.mark.asyncio

API_PATH = "custom_components.felicity_solar_local.coordinator.FelicityLocalClient.async_get_data"


async def test_setup_entry_creates_sensors_with_correct_state(
    hass: HomeAssistant, sample_response: dict[str, Any]
) -> None:
    serial = sample_response["DevSN"]
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=serial,
        data={CONF_HOST: "192.168.1.50", CONF_PORT: 53970},
    )
    entry.add_to_hass(hass)

    with patch(API_PATH, AsyncMock(return_value=sample_response)):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    registry = er.async_get(hass)

    voltage_entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{serial}_voltage")
    assert voltage_entity_id is not None
    voltage_state = hass.states.get(voltage_entity_id)
    assert voltage_state is not None
    assert float(voltage_state.state) == 54.04

    # Per-cell voltage sensors are registered but disabled by default (16 of them would
    # otherwise clutter the entity list) - confirm registration without expecting a state.
    cell_entity_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{serial}_cell_1_voltage"
    )
    assert cell_entity_id is not None
    assert registry.entities[cell_entity_id].disabled is True

    raw_entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{serial}_raw_data")
    assert raw_entity_id is not None
    raw_state = hass.states.get(raw_entity_id)
    assert raw_state is not None
    assert raw_state.attributes["profile"] == "FLB48314TG1-H"
    assert raw_state.attributes["profile_confidence"] == "verified"
    assert raw_state.attributes["raw"]["DevSN"] == serial


async def test_setup_entry_creates_charging_state_sensor(
    hass: HomeAssistant, sample_response: dict[str, Any]
) -> None:
    serial = sample_response["DevSN"]
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=serial,
        data={CONF_HOST: "192.168.1.50", CONF_PORT: 53970},
    )
    entry.add_to_hass(hass)

    with patch(API_PATH, AsyncMock(return_value=sample_response)):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{serial}_charging_state")
    assert entity_id is not None
    assert registry.entities[entity_id].disabled is False

    state = hass.states.get(entity_id)
    assert state is not None
    # sample_response.json's Bstate (9152) has bit 13 set -> charging.
    assert state.state == "charging"
    assert state.attributes["options"] == ["charging", "discharging", "standby"]
    assert state.attributes["device_class"] == "enum"


async def test_unload_entry(hass: HomeAssistant, sample_response: dict[str, Any]) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=sample_response["DevSN"],
        data={CONF_HOST: "192.168.1.50", CONF_PORT: 53970},
    )
    entry.add_to_hass(hass)

    with patch(API_PATH, AsyncMock(return_value=sample_response)):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state.value == "not_loaded"
