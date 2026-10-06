from typer.testing import CliRunner
from patchpilot.cli import app
from patchpilot import __version__

runner = CliRunner()

def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert f"PatchPilot v{__version__}" in result.stdout

def test_cli_models():
    result = runner.invoke(app, ["models"])
    assert result.exit_code == 0

def test_cli_diagnose_passing():
    result = runner.invoke(app, ["diagnose", "--cmd", "python3 -c 'exit(0)'"])
    assert result.exit_code == 0
    assert "All tests passed cleanly" in result.stdout
