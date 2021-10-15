from anchorpy.workspace import create_workspace
from anchorpy.program.context import Context
from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID

workspace = create_workspace()
program = workspace["basic_2"]
provider = program.provider


def test():
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
