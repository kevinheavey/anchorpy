"""Mimics anchor/examples/tutorial/basic-3/tests/basic-3.js."""
from typing import AsyncGenerator

from pytest import mark
from pytest_asyncio import fixture as async_fixture
from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID

from anchorpy import Provider, Context
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType


workspace = workspace_fixture("anchor/examples/tutorial/basic-3")


@async_fixture(scope="module")
async def provider() -> AsyncGenerator[Provider, None]:
    """Create a Provider instance."""
    prov = Provider.local()
    yield prov
    await prov.close()


@mark.asyncio
async def test_cpi(workspace: WorkspaceType, provider: Provider) -> None:
    """Test CPI from puppet master to puppet."""
    puppet_master = workspace["puppet_master"]
    puppet = workspace["puppet"]
    new_puppet_account = Keypair()
    await puppet.rpc["initialize"](
        ctx=Context(
            accounts={
                "puppet": new_puppet_account.public_key,
                "user": provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[new_puppet_account],
        ),
    )
    await puppet_master.rpc["pull_strings"](
        111,
        ctx=Context(
            accounts={
                "puppet": new_puppet_account.public_key,
                "puppet_program": puppet.program_id,
            },
        ),
    )
    puppet_account = await puppet.account["Data"].fetch(new_puppet_account.public_key)
    assert puppet_account.data == 111
