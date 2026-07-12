"""Diagnostics support for Felicity Solar Local."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import FelicityLocalConfigEntry
from .const import CONF_HOST

TO_REDACT = {CONF_HOST, "DevSN", "wifiSN"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: FelicityLocalConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "entry_options": dict(entry.options),
        "profile": coordinator.data.profile.name,
        "profile_confidence": coordinator.data.profile.confidence,
        "parsed_data": coordinator.data.data,
        "raw_data": async_redact_data(coordinator.data.raw, TO_REDACT),
    }
