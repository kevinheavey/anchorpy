"""Mimics anchor/examples/tutorial/basic-0/tests/basic-0.js."""
from pathlib import Path

from anchorpy import create_workspace
from anchorpy.pytest_plugin import localnet_fixture
from pytest import mark

PATH = Path("anchor/examples/tutorial/basic-0")

# We use localnet_fixture here to make sure it works, but use
# workspace_fixture elsewhere.
localnet = localnet_fixture(PATH)


@mark.asyncio
async def test_init(localnet) -> None:
    """Test that the initialize function is invoked successfully."""
    workspace = create_workspace(PATH)
    program = workspace["basic_0"]
    res = await program.rpc["initialize"]()
    assert res
    await program.close()
