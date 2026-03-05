"""CLI entry point for orcha-mcp."""

from __future__ import annotations

import typer

app = typer.Typer(help="Orcha — MCP orchestrator CLI.")


@app.command()
def run() -> None:
    """Run the orchestration."""
    typer.echo("Running Orcha...")


def main() -> None:
    """Invoke the Typer application."""
    app()


if __name__ == "__main__":
    main()
