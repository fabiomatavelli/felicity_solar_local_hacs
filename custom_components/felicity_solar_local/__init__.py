"""The Felicity Solar Local integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)
from .coordinator import FelicityLocalCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

type FelicityLocalConfigEntry = ConfigEntry[FelicityLocalCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: FelicityLocalConfigEntry) -> bool:
    """Set up Felicity Solar Local from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    update_interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    coordinator = FelicityLocalCoordinator(
        hass=hass,
        config_entry=entry,
        host=host,
        port=port,
        update_interval=update_interval,
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FelicityLocalConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: FelicityLocalConfigEntry) -> None:
    """Reload the entry when its options change (e.g. update_interval)."""
    await hass.config_entries.async_reload(entry.entry_id)
