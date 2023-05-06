"""Mimics anchor/examples/tutorial/basic-3/tests/basic-3.js."""
from pathlib import Path
from typing import AsyncGenerator

from anchorpy import Context
from anchorpy.pytest_plugin import bankrun_fixture
from anchorpy.workspace import WorkspaceType, close_workspace, create_workspace
from pytest import mark
from pytest_asyncio import fixture as async_fixture
from solders.bankrun import ProgramTestContext
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID

PATH = Path("anchor/examples/tutorial/basic-3")

bankrun = bankrun_fixture(PATH)


@async_fixture(scope="module")
async def workspace(bankrun: ProgramTestContext) -> AsyncGenerator[WorkspaceType, None]:
    ws = create_workspace(PATH)
    yield ws
    await close_workspace(ws)


@mark.asyncio
async def test_cpi(workspace: WorkspaceType, bankrun: ProgramTestContext) -> None:
    """Test CPI from puppet master to puppet."""
    puppet_master = workspace["puppet_master"]
    puppet = workspace["puppet"]
    new_puppet_account = Keypair()
    payer = bankrun.payer
    blockhash = bankrun.last_blockhash
    client = bankrun.banks_client
    tx0 = puppet.transaction["initialize"](
        payer=payer,
        blockhash=blockhash,
        ctx=Context(
            accounts={
                "puppet": new_puppet_account.pubkey(),
                "user": payer.pubkey(),
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[new_puppet_account],
        ),
    )
    await client.process_transaction(tx0)
    tx1 = puppet_master.transaction["pull_strings"](
        111,
        payer=payer,
        blockhash=blockhash,
        ctx=Context(
            accounts={
                "puppet": new_puppet_account.pubkey(),
                "puppet_program": puppet.program_id,
            },
        ),
    )
    await client.process_transaction(tx1)
    puppet_account_raw = await client.get_account(new_puppet_account.pubkey())
    assert puppet_account_raw is not None
    decoded = puppet.account["Data"].coder.accounts.decode(puppet_account_raw.data)
    assert decoded.data == 111
