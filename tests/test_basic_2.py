from pytest import fixture
from anchorpy.program.core import Program
from anchorpy.provider import Provider
from anchorpy.workspace import create_workspace
from anchorpy.program.context import Context
from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID


@fixture(scope="session")
def program() -> Program:
    return create_workspace()["basic_1"]


@fixture(scope="session")
def provider(program: Program) -> Provider:
    return program.provider


@fixture(scope="session")
def test_create_counter(program: Program, provider: Provider) -> Keypair:
    """Test creating a counter."""
    counter = Keypair()

    program.rpc["create"](
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
    counter_account = program.account["Counter"].fetch(counter.public_key)
    assert counter_account["authority"] == provider.wallet.public_key
    assert counter_account["count"] == 0
    return counter


def test_update_counter(
    test_create_counter: Keypair, program: Program, provider: Provider
) -> None:
    """Test updating the counter."""
    counter = test_create_counter
    program.rpc["increment"](
        ctx=Context(
            accounts={
                "counter": counter.public_key,
                "authority": provider.wallet.public_key,
            }
        )
    )
    counter_account = program.account["Counter"].fetch(counter.public_key)
    assert counter_account["authority"] == provider.wallet.public_key
    assert counter_account["count"] == 1
