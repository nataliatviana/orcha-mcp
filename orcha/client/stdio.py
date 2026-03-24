"""STDIO transport client for local MCP servers."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import InitializeResult

from orcha.config.schema import LocalServerConfig
from orcha.errors import ServerConnectionError


@dataclass
class ConnectedServer:
    """Holds the active session and negotiated data for a connected MCP server."""

    name: str
    session: ClientSession
    init_result: InitializeResult


@asynccontextmanager
async def connect_stdio(
    name: str,
    config: LocalServerConfig,
) -> AsyncIterator[ConnectedServer]:
    """Start a local MCP server subprocess and perform the MCP handshake.

    Starts the server process using ``config.command``, sends the ``initialize``
    request (with ``protocolVersion`` and ``clientInfo``), receives the server
    capabilities, and sends ``notifications/initialized`` — all via the MCP SDK.

    Args:
        name: Logical name for this server (the key used in ``orcha.json``).
        config: The server's configuration (command, environment flags, etc.).

    Yields:
        A :class:`ConnectedServer` with the active session and the
        :class:`~mcp.types.InitializeResult` returned by the server.

    Raises:
        ServerConnectionError: If the subprocess cannot be started because the
            command is not found or is otherwise unavailable.
    """
    env: dict[str, str] = {**dict(os.environ), **config.environment}
    params = StdioServerParameters(
        command=config.command[0],
        args=config.command[1:],
        env=env,
    )

    try:
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write) as session,
        ):
            init_result = await session.initialize()

            server_info = init_result.serverInfo
            capabilities = init_result.capabilities

            print("\n MCP Server Connected")
            print(f"Name: {server_info.name}")
            print(f"Version: {server_info.version}")
            print("Capabilities:")

            for cap in capabilities.model_dump().keys():
                print(f"- {cap}")

            yield ConnectedServer(
                name=name,
                session=session,
                init_result=init_result,
            )
    except FileNotFoundError as exc:
        raise ServerConnectionError(
            f"Server '{name}': command not found — '{config.command[0]}'. "
            "Make sure the command is installed and available in PATH."
        ) from exc
