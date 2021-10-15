from anchorpy.workspace import create_workspace
from anchorpy.program.context import Context
from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID

workspace = create_workspace()
program = workspace["basic_1"]


def test_create_and_initialize_account() -> None:
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

    program.rpc["update"](
        4321, ctx=Context(accounts={"myAccount": my_account.public_key})
    )

    account = program.account["MyAccount"].fetch(my_account.public_key)
    assert account["data"] == 4321
