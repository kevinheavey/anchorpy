import asyncio
from pytest import fixture, mark
from anchorpy import Program, Provider, create_workspace, close_workspace, Context
from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID


@fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@fixture(scope="session")
async def program() -> Program:
    workspace = create_workspace()
    yield workspace["basic_2"]
    await close_workspace(workspace)


@fixture(scope="session")
def provider(program: Program) -> Provider:
    return program.provider


@fixture(scope="session")
async def created_counter(program: Program, provider: Provider) -> Keypair:
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
    created_counter: Keypair, program: Program, provider: Provider
) -> None:
    """Test creating a counter."""
    counter_account = await program.account["Counter"].fetch(created_counter.public_key)
    assert counter_account["authority"] == provider.wallet.public_key
    assert counter_account["count"] == 0


@mark.asyncio
async def test_update_counter(
    created_counter: Keypair, program: Program, provider: Provider
) -> None:
    """Test updating the counter."""
    await program.rpc["increment"](
        ctx=Context(
            accounts={
                "counter": created_counter.public_key,
                "authority": provider.wallet.public_key,
            }
        )
    )
    counter_account = await program.account["Counter"].fetch(created_counter.public_key)
    assert counter_account["authority"] == provider.wallet.public_key
    assert counter_account["count"] == 1
