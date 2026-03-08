"""CLI entry point for orcha-mcp."""

from __future__ import annotations

import typer

from orcha.config import FULL_DEFAULT_CONFIG_PATH, load_config
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
def run(ctx: typer.Context) -> None:
    """Run the orchestration."""
    typer.echo("Running Orcha...")
    typer.echo(f"Configuration loaded successfully: {ctx.obj}")


def main() -> None:
    """Invoke the Typer application."""
    app()


if __name__ == "__main__":
    main()
