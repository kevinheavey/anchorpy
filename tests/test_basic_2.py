"""Mimics anchor/examples/tutorial/basic-2/tests/basic-2.js."""
from pathlib import Path
from typing import AsyncGenerator

from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID

from pytest import fixture, mark
from anchorpy import Program, Provider, create_workspace, close_workspace, Context
from anchorpy.pytest_plugin import get_localnet

PATH = Path("anchor/examples/tutorial/basic-2")

localnet = get_localnet(PATH)


@fixture(scope="module")
async def program(localnet) -> AsyncGenerator[Program, None]:
    """Create a Program instance."""
    workspace = create_workspace(PATH)
    yield workspace["basic_2"]
    await close_workspace(workspace)


@fixture(scope="module")
async def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    return program.provider


@fixture(scope="module")
async def created_counter(program: Program, provider: Provider) -> Keypair:
    """Create the counter."""
    counter = Keypair()
    await program.rpc["create"](
        provider.wallet.public_key,
        ctx=Context(
            accounts={
                "counter": counter.public_key,
                "user": provider.wallet.public_key,
                "systemProgram": SYS_PROGRAM_ID,
            },
            signers=[counter],
        ),
    )
    return counter


@mark.asyncio
async def test_create_counter(
    created_counter: Keypair,
    program: Program,
    provider: Provider,
) -> None:
    """Test creating a counter."""
    counter_account = await program.account["Counter"].fetch(created_counter.public_key)
    assert counter_account.authority == provider.wallet.public_key
    assert counter_account.count == 0


@mark.asyncio
async def test_update_counter(
    created_counter: Keypair,
    program: Program,
    provider: Provider,
) -> None:
    """Test updating the counter."""
    await program.rpc["increment"](
        ctx=Context(
            accounts={
                "counter": created_counter.public_key,
                "authority": provider.wallet.public_key,
            },
        ),
    )
    counter_account = await program.account["Counter"].fetch(created_counter.public_key)
    assert counter_account.authority == provider.wallet.public_key
    assert counter_account.count == 1
