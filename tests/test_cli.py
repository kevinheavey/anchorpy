"""Test that the CLI commands work."""

from pathlib import Path

from anchorpy import localnet_fixture
from anchorpy.cli import app
from solana.rpc.api import Client
from solana.rpc.commitment import Processed
from solders.signature import Signature
from typer.testing import CliRunner

PATH = Path("anchor/examples/tutorial/basic-0")

localnet = localnet_fixture(PATH)

runner = CliRunner()


def test_shell(localnet, monkeypatch) -> None:
    monkeypatch.chdir("anchor/examples/tutorial/basic-0")
    cli_input = "await workspace['basic_0'].rpc['initialize']()\nexit()"
    result = runner.invoke(app, ["shell"], input=cli_input)
    assert result.exit_code == 0
    assert "Hint: type `workspace`" in result.stdout
    tx_sig = Signature.from_string(
        result.stdout.split("Out[1]: \n")[1].split("\n    ")[1].split(",")[0]
    )
    client = Client()
    client.confirm_transaction(tx_sig, commitment=Processed)
