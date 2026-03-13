"""Tests for orcha.client.stdio — STDIO transport client."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp import StdioServerParameters
from mcp.types import Implementation, InitializeResult, ServerCapabilities

from orcha.client.stdio import ConnectedServer, connect_stdio
from orcha.config.schema import LocalServerConfig
from orcha.errors import ServerConnectionError


def _make_init_result() -> InitializeResult:
    """Build a minimal fake InitializeResult for unit tests."""
    return InitializeResult(
        protocolVersion="2024-11-05",
        capabilities=ServerCapabilities(),
        serverInfo=Implementation(name="fake-server", version="0.0.1"),
    )


def _make_mock_session(
    init_result: InitializeResult,
) -> tuple[MagicMock, MagicMock]:
    """Return (mock_session, mock_session_cm) for use as ClientSession CM."""
    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock(return_value=init_result)

    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)

    return mock_session, mock_session_cm


def _make_mock_stdio_cm() -> MagicMock:
    """Return a mock async context manager to replace stdio_client."""
    mock_read = MagicMock()
    mock_write = MagicMock()

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    return mock_cm


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_connect_stdio_yields_connected_server() -> None:
    """connect_stdio yields a ConnectedServer with correct name and init_result."""
    config = LocalServerConfig(type="local", command=["fake-cmd", "--arg"])
    init_result = _make_init_result()
    mock_session, mock_session_cm = _make_mock_session(init_result)

    with (
        patch("orcha.client.stdio.stdio_client", return_value=_make_mock_stdio_cm()),
        patch("orcha.client.stdio.ClientSession", return_value=mock_session_cm),
    ):
        async with connect_stdio("my-server", config) as server:
            assert isinstance(server, ConnectedServer)
            assert server.name == "my-server"
            assert server.session is mock_session
            assert server.init_result is init_result


@pytest.mark.anyio
async def test_connect_stdio_calls_initialize() -> None:
    """connect_stdio calls session.initialize() exactly once."""
    config = LocalServerConfig(type="local", command=["fake-cmd"])
    init_result = _make_init_result()
    mock_session, mock_session_cm = _make_mock_session(init_result)

    with (
        patch("orcha.client.stdio.stdio_client", return_value=_make_mock_stdio_cm()),
        patch("orcha.client.stdio.ClientSession", return_value=mock_session_cm),
    ):
        async with connect_stdio("s", config):
            pass

    mock_session.initialize.assert_awaited_once()


@pytest.mark.anyio
async def test_connect_stdio_merges_environment() -> None:
    """connect_stdio passes merged env dict to StdioServerParameters."""
    config = LocalServerConfig(
        type="local",
        command=["fake-cmd"],
        environment={"CUSTOM_VAR": "custom_value"},
    )
    init_result = _make_init_result()
    _, mock_session_cm = _make_mock_session(init_result)

    captured_params: list[Any] = []

    def fake_stdio_client(params: Any) -> MagicMock:
        captured_params.append(params)
        return _make_mock_stdio_cm()

    with (
        patch("orcha.client.stdio.stdio_client", side_effect=fake_stdio_client),
        patch("orcha.client.stdio.ClientSession", return_value=mock_session_cm),
    ):
        async with connect_stdio("s", config):
            pass

    assert len(captured_params) == 1
    params = captured_params[0]
    assert isinstance(params, StdioServerParameters)
    assert params.env is not None
    assert params.env["CUSTOM_VAR"] == "custom_value"


@pytest.mark.anyio
async def test_connect_stdio_splits_command_into_exec_and_args() -> None:
    """connect_stdio splits command[0] as executable and command[1:] as args."""
    config = LocalServerConfig(
        type="local",
        command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "."],
    )
    init_result = _make_init_result()
    _, mock_session_cm = _make_mock_session(init_result)

    captured_params: list[Any] = []

    def fake_stdio_client(params: Any) -> MagicMock:
        captured_params.append(params)
        return _make_mock_stdio_cm()

    with (
        patch("orcha.client.stdio.stdio_client", side_effect=fake_stdio_client),
        patch("orcha.client.stdio.ClientSession", return_value=mock_session_cm),
    ):
        async with connect_stdio("filesystem", config):
            pass

    params = captured_params[0]
    assert isinstance(params, StdioServerParameters)
    assert params.command == "npx"
    assert params.args == ["-y", "@modelcontextprotocol/server-filesystem", "."]


@pytest.mark.anyio
async def test_connect_stdio_raises_server_connection_error_on_file_not_found() -> None:
    """connect_stdio wraps FileNotFoundError as ServerConnectionError."""
    config = LocalServerConfig(type="local", command=["nonexistent-binary"])

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(side_effect=FileNotFoundError("No such file"))
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("orcha.client.stdio.stdio_client", return_value=mock_cm),
        pytest.raises(ServerConnectionError) as exc_info,
    ):
        async with connect_stdio("broken-server", config):
            pass

    error_msg = str(exc_info.value)
    assert "broken-server" in error_msg
    assert "nonexistent-binary" in error_msg


# ---------------------------------------------------------------------------
# Integration tests — require external processes; skipped by default.
# Run with: uv run pytest -m integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_connect_stdio_handshake_with_filesystem_server() -> None:
    """Full handshake with @modelcontextprotocol/server-filesystem via npx.

    Requires Node.js / npx to be available in PATH.
    """
    config = LocalServerConfig(
        type="local",
        command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "."],
    )

    async with connect_stdio("filesystem", config) as server:
        assert server.name == "filesystem"
        assert server.init_result is not None
        assert server.init_result.capabilities is not None
        assert server.init_result.serverInfo is not None
