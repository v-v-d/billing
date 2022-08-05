from typer.testing import CliRunner

from manage import typer_app

runner = CliRunner()


def test_shell():
    result = runner.invoke(typer_app, ["shell"])
    assert result.exit_code == 0
