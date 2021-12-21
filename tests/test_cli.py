"""Test that the CLI commands work."""

import subprocess
from pathlib import Path

from pytest import fixture
from typer.testing import CliRunner
from solana.rpc.api import Client
from solana.rpc.commitment import Processed

from anchorpy import localnet_fixture
from anchorpy.cli import app

PATH = Path("anchor/examples/tutorial/basic-0")
PROJECT_NAME = "foo"

localnet = localnet_fixture(PATH)

runner = CliRunner()


def test_shell(localnet, monkeypatch) -> None:
    monkeypatch.chdir("anchor/examples/tutorial/basic-0")
    cli_input = "await workspace['basic_0'].rpc['initialize']()\nexit()"
    result = runner.invoke(app, ["shell"], input=cli_input)
    assert result.exit_code == 0
    assert "Hint: type `workspace`" in result.stdout
    tx_sig = result.stdout.split("Out[1]: '")[1].split("'")[0]
    client = Client()
    client.confirm_transaction(tx_sig, commitment=Processed)


@fixture(scope="session")
def project_parent_dir(tmpdir_factory) -> Path:
    return Path(tmpdir_factory.mktemp("temp"))


@fixture(scope="session")
def project_dir(project_parent_dir: Path) -> Path:
    subprocess.run(["anchor", "init", PROJECT_NAME], cwd=project_parent_dir, check=True)
    proj_dir = project_parent_dir / PROJECT_NAME
    subprocess.run(["anchor", "build"], cwd=proj_dir, check=True)
    subprocess.run(["anchorpy", "init", PROJECT_NAME], cwd=proj_dir, check=True)
    return proj_dir


def test_init(project_dir: Path):
    subprocess.run("pytest", cwd=project_dir, check=True)
