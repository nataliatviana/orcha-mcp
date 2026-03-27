from typer.testing import CliRunner
from orcha.cli import app


def test_run_outputs_handshake():
    runner = CliRunner()

    result = runner.invoke(app, ["run"])

    assert result.exit_code == 0
    assert "Server:" in result.output
    assert "Version:" in result.output
    assert "Capabilities:" in result.output