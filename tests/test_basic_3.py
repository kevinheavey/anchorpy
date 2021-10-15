from anchorpy.workspace import create_workspace
from anchorpy.provider import Provider
from anchorpy.program.context import Context
from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID

workspace = create_workspace()
provider = Provider.local()


def test() -> None:
    puppet_master = workspace["puppet_master"]
    puppet = workspace["puppet"]
    new_puppet_account = Keypair()
    puppet.rpc["initialize"](
        ctx=Context(
            accounts={
                "puppet": new_puppet_account.public_key,
                "user": provider.wallet.public_key,
                "systemProgram": SYS_PROGRAM_ID,
            },
            signers=[new_puppet_account],
        )
    )
    puppet_master.transaction["pullStrings"](
        111,
        ctx=Context(
            accounts={
                "puppet": new_puppet_account.public_key,
                "puppetProgram": puppet.program_id,
            }
        ),
    )
    puppet_master.rpc["pullStrings"](
        111,
        ctx=Context(
            accounts={
                "puppet": new_puppet_account.public_key,
                "puppetProgram": puppet.program_id,
            }
        ),
    )
    puppet_account = puppet.account["Data"].fetch(new_puppet_account.public_key)
    assert puppet_account["data"] == 111
