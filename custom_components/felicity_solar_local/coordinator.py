"""DataUpdateCoordinator for a single Felicity Solar local battery."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FelicityLocalClient, FelicityLocalError
from .const import DEFAULT_TIMEOUT, DOMAIN
from .profiles import BatteryProfile, select_profile

_LOGGER = logging.getLogger(__name__)


@dataclass
class FelicityBatteryData:
    """Latest snapshot for a battery: raw response, matched profile, and parsed values."""

    raw: dict[str, Any]
    profile: BatteryProfile
    data: dict[str, Any]


class FelicityLocalCoordinator(DataUpdateCoordinator[FelicityBatteryData]):
    """Coordinator that polls one battery over its local TCP/JSON endpoint."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        host: str,
        port: int,
        update_interval: int,
        persistent_connection: bool = False,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{host}",
            update_interval=timedelta(seconds=update_interval),
        )
        self.host = host
        self.port = port
        self.client = FelicityLocalClient(
            host, port, timeout=DEFAULT_TIMEOUT, persistent=persistent_connection
        )
        self._tz_offset_minutes: int | None = None
        self._tz_offset_fetched = False

    async def _async_update_data(self) -> FelicityBatteryData:
        try:
            raw = await self.client.async_get_data()
        except FelicityLocalError as err:
            raise UpdateFailed(
                f"Error communicating with battery at {self.host}:{self.port}: {err}"
            ) from err

        # The device's own UTC offset rarely changes (only across DST transitions), so
        # this is fetched once per coordinator lifetime rather than every poll - it's a
        # separate command from the main query above, but reuses the same connection in
        # persistent mode (see api.py) rather than opening a second one.
        if not self._tz_offset_fetched:
            self._tz_offset_minutes = await self.client.async_get_timezone_offset_minutes()
            self._tz_offset_fetched = True
        if self._tz_offset_minutes is not None:
            raw = {**raw, "timeZMin": self._tz_offset_minutes}

        profile = select_profile(raw)
        return FelicityBatteryData(raw=raw, profile=profile, data=profile.parse(raw))
