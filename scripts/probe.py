#!/usr/bin/env python3
"""Probe a Felicity Solar battery's local WiFi endpoint and dump its raw snapshot.

Standalone (stdlib-only) - does not require Home Assistant or the integration installed.
Useful for confirming the protocol works against a given battery before setting up the
integration, and for capturing a fixture to build/verify a battery-model profile.

Usage: python3 scripts/probe.py <host> [port]
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import sys

DEFAULT_PORT = 53970
QUERY_COMMAND = b"wifilocalMonitor:get dev real infor"
ACK_BYTE = b"."
TIMEOUT = 5.0


async def probe(host: str, port: int) -> None:
    print(f"Connecting to {host}:{port} ...")
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(host, port), timeout=TIMEOUT
    )

    try:
        writer.write(QUERY_COMMAND)
        await asyncio.wait_for(writer.drain(), timeout=TIMEOUT)

        buffer = b""
        while b"}" not in buffer:
            chunk = await asyncio.wait_for(reader.read(4096), timeout=TIMEOUT)
            if not chunk:
                break
            buffer += chunk

        if b"}" not in buffer:
            print(f"No closing brace received. Raw buffer: {buffer!r}")
            return

        payload = buffer[: buffer.index(b"}") + 1]
        data = json.loads(payload)

        print(f"\nType={data.get('Type')} SubType={data.get('SubType')} "
              f"DevSN={data.get('DevSN')}\n")
        print(json.dumps(data, indent=2))

        writer.write(ACK_BYTE)
        await asyncio.wait_for(writer.drain(), timeout=TIMEOUT)
    finally:
        writer.close()
        with contextlib.suppress(TimeoutError, OSError):
            await asyncio.wait_for(writer.wait_closed(), timeout=TIMEOUT)


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <host> [port]")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT

    try:
        asyncio.run(probe(host, port))
    except (TimeoutError, OSError) as err:
        print(f"Failed to probe {host}:{port}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
