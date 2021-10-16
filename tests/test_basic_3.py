from typing import Dict
import asyncio
from pytest import mark, fixture
from anchorpy import create_workspace, close_workspace, Provider, Context
from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID
from anchorpy.program.core import Program


@fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@fixture(scope="session")
async def workspace():
    ws = create_workspace()
    yield ws
    await close_workspace(ws)


@fixture(scope="session")
async def provider() -> Provider:
    prov = Provider.local()
    yield prov
    await prov.close()


@mark.asyncio
async def test_cpi(workspace: Dict[str, Program], provider: Provider) -> None:
    """Test CPI from puppet master to puppet."""
    puppet_master = workspace["puppet_master"]
    puppet = workspace["puppet"]
    new_puppet_account = Keypair()
    await puppet.rpc["initialize"](
        ctx=Context(
            accounts={
                "puppet": new_puppet_account.public_key,
                "user": provider.wallet.public_key,
                "systemProgram": SYS_PROGRAM_ID,
            },
            signers=[new_puppet_account],
        )
    )
    await puppet_master.rpc["pullStrings"](
        111,
        ctx=Context(
            accounts={
                "puppet": new_puppet_account.public_key,
                "puppetProgram": puppet.program_id,
            }
        ),
    )
    puppet_account = await puppet.account["Data"].fetch(new_puppet_account.public_key)
    assert puppet_account["data"] == 111
