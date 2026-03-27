"""STDIO transport client for local MCP servers."""

from __future__ import annotations

import os
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import typer
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
    verbose: bool = False,
) -> AsyncIterator[ConnectedServer]:
    """Start a local MCP server subprocess and perform the MCP handshake."""

    # 🔐 merge env (task anterior)
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
            # handshake MCP
            init_result = await session.initialize()

            server_info = init_result.serverInfo
            capabilities = init_result.capabilities

            
            typer.echo("\n=== MCP Server Connected ===")
            typer.echo(f"Server: {server_info.name}")
            typer.echo(f"Version: {server_info.version}")
            typer.echo("Capabilities:")

            for key, value in capabilities.model_dump().items():
                if value:
                    typer.echo(f"  - {key}")

            # verbose → JSON-RPC completo
            if verbose:
                typer.echo("\n🔍 RAW INITIALIZE RESPONSE:")
                typer.echo(json.dumps(init_result.model_dump(), indent=2))

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