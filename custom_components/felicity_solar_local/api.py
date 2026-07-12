"""TCP/JSON client for the Felicity Solar battery local WiFi protocol.

Protocol reverse-engineered from https://github.com/mxbode/Felicitysolar-FLA48300-WiFi-Readout
(no license on that repo, so this is a fresh implementation from the observed protocol facts,
not a port of its code) and confirmed live against a Felicity Solar FLB48314TG1-H:

- Plain TCP on port 53970, no TLS, no Modbus framing.
- Write the ASCII command ``wifilocalMonitor:get dev real infor`` (no newline needed).
- The device replies with a single JSON object. The payload never nests ``{}``, only ``[]``,
  so reading up to and including the first ``}`` yields the complete, valid JSON document.
- After parsing, write a single ``.`` byte back to the device as an acknowledgement before
  closing the connection - the device does not always send a clean EOF.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any

from .const import ACK_BYTE, DEFAULT_PORT, DEFAULT_TIMEOUT, QUERY_COMMAND

_LOGGER = logging.getLogger(__name__)

# The firmware reports a zero pack voltage when a read happens mid-boot/mid-update.
# Treat that as an invalid snapshot rather than publishing a zeroed voltage.
_PACK_VOLTAGE_PATH = ("Batt", 0, 0)


class FelicityLocalError(Exception):
    """Base error for the Felicity Solar local client."""


class FelicityConnectionError(FelicityLocalError):
    """Raised when the TCP connection to the battery cannot be established."""


class FelicityTimeoutError(FelicityLocalError):
    """Raised when the battery does not respond within the configured timeout."""


class FelicityProtocolError(FelicityLocalError):
    """Raised when the battery's response is not valid/usable JSON."""


def _extract_path(data: dict[str, Any], path: tuple[str, int, int]) -> Any:
    key, row, col = path
    try:
        return data[key][row][col]
    except (KeyError, IndexError, TypeError):
        return None


class FelicityLocalClient:
    """Async client for a single Felicity Solar battery's local WiFi endpoint."""

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    async def async_get_data(self) -> dict[str, Any]:
        """Query the battery and return the parsed JSON payload."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )
        except TimeoutError as err:
            raise FelicityTimeoutError(
                f"Timed out connecting to {self.host}:{self.port}"
            ) from err
        except OSError as err:
            raise FelicityConnectionError(
                f"Could not connect to {self.host}:{self.port}: {err}"
            ) from err

        try:
            data = await self._query(reader, writer)
        finally:
            writer.close()
            with contextlib.suppress(TimeoutError, OSError):
                await asyncio.wait_for(writer.wait_closed(), timeout=self.timeout)

        voltage = _extract_path(data, _PACK_VOLTAGE_PATH)
        if not voltage:
            raise FelicityProtocolError(
                f"Battery at {self.host}:{self.port} returned an invalid/empty snapshot "
                f"(pack voltage missing or zero)"
            )

        return data

    async def _query(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> dict[str, Any]:
        writer.write(QUERY_COMMAND)
        try:
            await asyncio.wait_for(writer.drain(), timeout=self.timeout)
        except OSError as err:
            raise FelicityConnectionError(f"Failed to send query: {err}") from err

        buffer = b""
        try:
            while b"}" not in buffer:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=self.timeout)
                if not chunk:
                    break
                buffer += chunk
        except TimeoutError as err:
            raise FelicityTimeoutError(
                f"Timed out waiting for response from {self.host}:{self.port}"
            ) from err
        except OSError as err:
            raise FelicityConnectionError(f"Connection error while reading: {err}") from err

        if b"}" not in buffer:
            raise FelicityProtocolError(
                f"Response from {self.host}:{self.port} was never terminated with '}}'"
            )

        payload = buffer[: buffer.index(b"}") + 1]

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as err:
            raise FelicityProtocolError(f"Could not parse response as JSON: {err}") from err

        if not isinstance(data, dict):
            raise FelicityProtocolError("Response JSON was not an object")

        # Best-effort ack; the battery doesn't require it for us to have already gotten
        # a valid reading, so a failure here shouldn't fail the whole update.
        try:
            writer.write(ACK_BYTE)
            await asyncio.wait_for(writer.drain(), timeout=self.timeout)
        except (TimeoutError, OSError):
            _LOGGER.debug(
                "Failed to send ack byte to %s:%s (non-fatal)", self.host, self.port
            )

        return data
