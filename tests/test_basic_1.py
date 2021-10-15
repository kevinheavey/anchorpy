from pytest import fixture, mark
from anchorpy import create_workspace, Context, Program
from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID


@mark.integration
@fixture(scope="session")
def program() -> Program:
    return create_workspace()["basic_1"]


@mark.integration
@fixture(scope="session")
def test_create_and_initialize_account(program: Program) -> Keypair:
    """Test creating and initializing account in single tx."""
    my_account = Keypair()
    program.rpc["initialize"](
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
    account = program.account["MyAccount"].fetch(my_account.public_key)
    assert account["data"] == 1234
    return my_account


@mark.integration
def test_update_previously_created_account(
    test_create_and_initialize_account: Keypair, program: Program
) -> None:
    """Test updating a previously created account."""
    my_account = test_create_and_initialize_account
    program.rpc["update"](
        4321, ctx=Context(accounts={"myAccount": my_account.public_key})
    )
    account = program.account["MyAccount"].fetch(my_account.public_key)
    assert account["data"] == 4321
