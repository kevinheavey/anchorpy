from pathlib import Path
from pytest import mark
from anchorpy import create_workspace
from tests.utils import get_localnet

PATH = Path("/home/kheavey/anchor/examples/tutorial/basic-0")


localnet = get_localnet(PATH)


@mark.asyncio
async def test_init(localnet) -> None:
    """Test that the initialize function is invoked successfully."""
    workspace = create_workspace(PATH)
    program = workspace["basic_0"]
    res = await program.rpc["initialize"]()
    assert res
    await program.close()
