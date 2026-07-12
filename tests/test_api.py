"""Tests for the Felicity Solar local TCP/JSON client."""

from __future__ import annotations

import asyncio
import json
import socket
from collections.abc import AsyncIterator
from typing import Any

import pytest

from custom_components.felicity_solar_local.api import (
    FelicityConnectionError,
    FelicityLocalClient,
    FelicityProtocolError,
    FelicityTimeoutError,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.enable_socket]


class _FakeServer:
    """A minimal TCP server that replays a canned response for one connection."""

    def __init__(self) -> None:
        self.received_command: bytes | None = None
        self.received_ack: bytes | None = None
        self.port: int | None = None
        self.handled = asyncio.Event()
        self._server: asyncio.AbstractServer | None = None
        self._response: bytes = b""
        self._hold_open = False

    async def start(self, response: bytes, hold_open: bool = False) -> int:
        self._response = response
        self._hold_open = hold_open
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]
        return self.port

    async def _handle(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        self.received_command = await reader.read(1024)
        if self._hold_open:
            # Simulate a device that never replies, to exercise the read timeout.
            await asyncio.sleep(10)
            return
        writer.write(self._response)
        await writer.drain()
        self.received_ack = await reader.read(1)
        writer.close()
        self.handled.set()

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()


@pytest.fixture
async def fake_server() -> AsyncIterator[_FakeServer]:
    server = _FakeServer()
    yield server
    await server.stop()


async def test_async_get_data_parses_response_and_sends_ack(
    fake_server: _FakeServer, sample_response: dict[str, Any]
) -> None:
    port = await fake_server.start(json.dumps(sample_response).encode())

    client = FelicityLocalClient("127.0.0.1", port, timeout=2.0)
    result = await client.async_get_data()
    await asyncio.wait_for(fake_server.handled.wait(), timeout=2.0)

    assert result["DevSN"] == sample_response["DevSN"]
    assert fake_server.received_command == b"wifilocalMonitor:get dev real infor"
    assert fake_server.received_ack == b"."


async def test_async_get_data_ignores_trailing_bytes_after_first_brace(
    fake_server: _FakeServer, sample_response: dict[str, Any]
) -> None:
    # The device is not guaranteed to close cleanly right after the closing brace;
    # the client must stop reading at the first '}' regardless of what follows.
    payload = json.dumps(sample_response).encode() + b"garbage-after-close"
    port = await fake_server.start(payload)

    client = FelicityLocalClient("127.0.0.1", port, timeout=2.0)
    result = await client.async_get_data()

    assert result["DevSN"] == sample_response["DevSN"]


async def test_async_get_data_raises_on_malformed_json(fake_server: _FakeServer) -> None:
    port = await fake_server.start(b'{"Batt": [[54000]], "not valid json"}')

    client = FelicityLocalClient("127.0.0.1", port, timeout=2.0)
    with pytest.raises(FelicityProtocolError):
        await client.async_get_data()


async def test_async_get_data_raises_on_zero_pack_voltage(
    fake_server: _FakeServer, sample_response: dict[str, Any]
) -> None:
    invalid = {**sample_response, "Batt": [[0], [0], [None]]}
    port = await fake_server.start(json.dumps(invalid).encode())

    client = FelicityLocalClient("127.0.0.1", port, timeout=2.0)
    with pytest.raises(FelicityProtocolError):
        await client.async_get_data()


async def test_async_get_data_raises_on_read_timeout(fake_server: _FakeServer) -> None:
    port = await fake_server.start(b"", hold_open=True)

    client = FelicityLocalClient("127.0.0.1", port, timeout=0.2)
    with pytest.raises(FelicityTimeoutError):
        await client.async_get_data()


async def test_async_get_data_raises_on_connection_refused() -> None:
    # Bind a real socket and close it immediately: connecting to the just-freed port
    # deterministically yields a fast connection-refused everywhere. An arbitrary
    # unbound port number (e.g. a low privileged one) isn't reliable for this across
    # platforms/Python versions - some environments don't refuse it promptly.
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()

    client = FelicityLocalClient("127.0.0.1", port, timeout=2.0)
    with pytest.raises(FelicityConnectionError):
        await client.async_get_data()
