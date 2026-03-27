"""CLI entry point for orcha-mcp."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import anyio
import typer

from orcha.client.stdio import connect_stdio
from orcha.config import FULL_DEFAULT_CONFIG_PATH, get_enabled_servers, load_config
from orcha.errors import InvalidConfigFileError
from orcha.config.schema import LocalServerConfig

app = typer.Typer(help="Orcha — MCP orchestrator CLI.")


# tipagem do contexto
class AppContext(TypedDict):
    config: dict
    verbose: bool


@app.callback()
def load_global_config(
    ctx: typer.Context,
    config: str | None = typer.Option(None, "--config", help="Path to config file"),
    verbose: bool = typer.Option(False, "--verbose", help="Show detailed logs"),
) -> None:
    """Load the global configuration."""
    try:
        if config:
            path = Path(config).resolve()

            if not path.exists():
                typer.echo(f"Config file not found: {config}")
                raise typer.Exit(code=1)

            loaded_config = load_config(
                file_path=Path(path.name),
                dir_path=path.parent,
            )
        else:
            loaded_config = load_config()

        ctx.obj = {
            "config": loaded_config,
            "verbose": verbose,
        }

    except InvalidConfigFileError as e:
        typer.echo(e.message)
        typer.echo(
            f"Invalid configuration. Please check your config file: "
            f"{FULL_DEFAULT_CONFIG_PATH}"
        )
        raise typer.Exit(code=1) from e


@app.command()
def run(
    ctx: typer.Context,
    server: str | None = typer.Option(
        None,
        "--server",
        help="Run only a specific MCP server",
    ),
) -> None:
    """Run the orchestration."""

    # proteção contra ctx vazio
    if ctx.obj is None:
        typer.echo("Configuration not loaded.")
        raise typer.Exit(code=1)

    context: AppContext = ctx.obj
    config = context["config"]
    verbose = context["verbose"]

    servers = config.get("mcps", {})

    if server:
        if server not in servers:
            typer.echo(f"Server '{server}' not found in configuration.")
            raise typer.Exit(code=1)

        selected_servers = {server: servers[server]}
    else:
        selected_servers = get_enabled_servers(config)

    typer.echo("\nServers to run:")

    for name in selected_servers:
        typer.echo(f"- {name}")

    # dispara handshake
    async def run_servers() -> None:
        for name, server_config in selected_servers.items():
            if server_config.get("type") == "local":
                typed_config = LocalServerConfig(**server_config)

                async with connect_stdio(name, typed_config, verbose=verbose):
                    pass

    anyio.run(run_servers)


def main() -> None:
    """Invoke the Typer application."""
    app()


if __name__ == "__main__":
    main()