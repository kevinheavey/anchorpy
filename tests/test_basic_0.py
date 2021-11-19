"""Mimics anchor/examples/tutorial/basic-0/tests/basic-0.js."""
from pathlib import Path
import subprocess

from pytest import mark

from anchorpy import create_workspace
from anchorpy.pytest_plugin import localnet_fixture

PATH = Path("anchor/examples/tutorial/basic-0")


localnet = localnet_fixture(PATH)


@mark.asyncio
async def test_init(localnet) -> None:
    """Test that the initialize function is invoked successfully."""
    workspace = create_workspace(PATH)
    program = workspace["basic_0"]
    res = await program.rpc["initialize"]()
    assert res
    await program.close()


@mark.asyncio
async def test_at_constructor(localnet) -> None:
    """Test that the Program.at classmethod works."""
    workspace = create_workspace(PATH)
    program = workspace["basic_0"]
    idl_path = "target/idl/basic_0.json"
    subprocess.run(  # noqa: S607,S603
        ["anchor", "idl", "init", "-f", idl_path, str(program.program_id)],
        cwd=PATH,
    )
    fetched = await program.at(program.program_id, program.provider)
    await program.close()
    assert fetched.idl.name == "basic_0"
