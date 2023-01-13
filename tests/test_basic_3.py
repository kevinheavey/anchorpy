"""Mimics anchor/examples/tutorial/basic-3/tests/basic-3.js."""
from typing import AsyncGenerator

from anchorpy import Context, Provider
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType
from pytest import mark
from pytest_asyncio import fixture as async_fixture
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID

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
                "puppet": new_puppet_account.pubkey(),
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
                "puppet": new_puppet_account.pubkey(),
                "puppet_program": puppet.program_id,
            },
        ),
    )
    puppet_account = await puppet.account["Data"].fetch(new_puppet_account.pubkey())
    assert puppet_account.data == 111
