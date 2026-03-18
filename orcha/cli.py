"""CLI entry point for orcha-mcp."""

from __future__ import annotations

import typer

from orcha.config import FULL_DEFAULT_CONFIG_PATH, get_enabled_servers, load_config
from orcha.errors import InvalidConfigFileError

app = typer.Typer(help="Orcha — MCP orchestrator CLI.")


@app.callback()
def load_global_config(ctx: typer.Context) -> None:
    """Load the global configuration."""
    try:
        config = load_config()
        ctx.obj = config
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

    config = ctx.obj
    servers = config.get("mcps", {})

    if server:
        if server not in servers:
            typer.echo(f"Server '{server}' not found in configuration.")
            raise typer.Exit(code=1)

        selected_servers = {server: servers[server]}
    else:
        selected_servers = get_enabled_servers(config)

    typer.echo("Servers to run:")

    for name in selected_servers:
        typer.echo(f"- {name}")


def main() -> None:
    """Invoke the Typer application."""
    app()


if __name__ == "__main__":
    main()
