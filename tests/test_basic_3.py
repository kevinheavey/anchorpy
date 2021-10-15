from pytest import mark
from anchorpy import create_workspace, Provider, Context
from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID


@mark.integration
def test_cpi() -> None:
    """Test CPI from puppet master to puppet."""
    workspace = create_workspace()
    provider = Provider.local()
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
