import asyncio
from pathlib import Path
from pytest import fixture, mark
from anchorpy import create_workspace, close_workspace, Context, Program
from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID
from tests.utils import get_localnet

PATH = Path("/home/kheavey/anchor/examples/tutorial/basic-1")

localnet = get_localnet(PATH)

# Since our other fixtures have module scope, we need to define
# this event_loop fixture and give it module scope otherwise
# pytest-asyncio will break.


@fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@fixture(scope="module")
async def program(localnet) -> Program:
    workspace = create_workspace(PATH)
    yield workspace["basic_1"]
    await close_workspace(workspace)


@fixture(scope="module")
async def initialized_account(program: Program) -> Keypair:
    my_account = Keypair()
    await program.rpc["initialize"](
        1234,
        ctx=Context(
            accounts={
                "myAccount": my_account.public_key,
                "user": program.provider.wallet.public_key,
                "systemProgram": SYS_PROGRAM_ID,
            },
            signers=[my_account],
        ),
    )
    return my_account


@mark.asyncio
async def test_create_and_initialize_account(
    program: Program, initialized_account: Keypair
) -> None:
    """Test creating and initializing account in single tx."""
    account = await program.account["MyAccount"].fetch(initialized_account.public_key)
    assert account["data"] == 1234


@mark.asyncio
async def test_update_previously_created_account(
    initialized_account: Keypair, program: Program
) -> None:
    """Test updating a previously created account."""
    await program.rpc["update"](
        4321, ctx=Context(accounts={"myAccount": initialized_account.public_key})
    )
    account = await program.account["MyAccount"].fetch(initialized_account.public_key)
    assert account["data"] == 4321
