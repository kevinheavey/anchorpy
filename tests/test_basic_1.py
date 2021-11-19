"""Mimics anchor/examples/tutorial/basic-1/tests/basic-1.js."""
from pathlib import Path
from typing import AsyncGenerator

from pytest import fixture, mark
from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID

from anchorpy import create_workspace, close_workspace, Context, Program
from anchorpy.pytest_plugin import localnet_fixture

PATH = Path("anchor/examples/tutorial/basic-1")

localnet = localnet_fixture(PATH)


@fixture(scope="module")
async def program(localnet) -> AsyncGenerator[Program, None]:
    """Create a Program instance."""
    workspace = create_workspace(PATH)
    yield workspace["basic_1"]
    await close_workspace(workspace)


@fixture(scope="module")
async def initialized_account(program: Program) -> Keypair:
    """Generate a keypair and initialize it."""
    my_account = Keypair()
    await program.rpc["initialize"](
        1234,
        ctx=Context(
            accounts={
                "my_account": my_account.public_key,
                "user": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[my_account],
        ),
    )
    return my_account


@mark.asyncio
async def test_create_and_initialize_account(
    program: Program,
    initialized_account: Keypair,
) -> None:
    """Test creating and initializing account in single tx."""
    account = await program.account["MyAccount"].fetch(initialized_account.public_key)
    assert account.data == 1234


@mark.asyncio
async def test_update_previously_created_account(
    initialized_account: Keypair,
    program: Program,
) -> None:
    """Test updating a previously created account."""
    await program.rpc["update"](
        4321,
        ctx=Context(accounts={"my_account": initialized_account.public_key}),
    )
    account = await program.account["MyAccount"].fetch(initialized_account.public_key)
    assert account.data == 4321
