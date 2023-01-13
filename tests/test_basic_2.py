"""Mimics anchor/examples/tutorial/basic-2/tests/basic-2.js."""

from anchorpy import Context, Program, Provider
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType
from pytest import fixture, mark
from pytest_asyncio import fixture as async_fixture
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID

workspace = workspace_fixture("anchor/examples/tutorial/basic-2")


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    """Create a Program instance."""
    return workspace["basic_2"]


@fixture(scope="module")
def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    return program.provider


@async_fixture(scope="module")
async def created_counter(program: Program, provider: Provider) -> Keypair:
    """Create the counter."""
    counter = Keypair()
    await program.rpc["create"](
        provider.wallet.public_key,
        ctx=Context(
            accounts={
                "counter": counter.pubkey(),
                "user": provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
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
    counter_account = await program.account["Counter"].fetch(created_counter.pubkey())
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
                "counter": created_counter.pubkey(),
                "authority": provider.wallet.public_key,
            },
        ),
    )
    counter_account = await program.account["Counter"].fetch(created_counter.pubkey())
    assert counter_account.authority == provider.wallet.public_key
    assert counter_account.count == 1
