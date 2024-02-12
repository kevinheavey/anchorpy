"""Mimics anchor/tests/misc/tests/misc.js."""
import asyncio
import subprocess
from pathlib import Path

from anchorpy import Context, Program
from anchorpy.error import ProgramError
from anchorpy.provider import Provider, Wallet
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.utils.rpc import invoke
from anchorpy.workspace import WorkspaceType
from pytest import fixture, mark, raises
from pytest_asyncio import fixture as async_fixture
from solana.rpc.core import RPCNoResultException
from solana.rpc.types import MemcmpOpts
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT

PATH = Path("anchor/tests/misc/")
# bankrun = bankrun_fixture(PATH, build_cmd="anchor build --skip-lint")
workspace = workspace_fixture(PATH, build_cmd="anchor build --skip-lint")


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    return workspace["misc"]


def test_methods(program: Program, initialized_keypair: Keypair) -> None:
    ix_from_methods = (
        program.methods["test_close"]
        .accounts(
            {
                "data": initialized_keypair.pubkey(),
                "sol_dest": initialized_keypair.pubkey(),
            }
        )
        .instruction()
    )
    ix_legacy = program.instruction["test_close"](
        ctx=Context(
            accounts={
                "data": initialized_keypair.pubkey(),
                "sol_dest": initialized_keypair.pubkey(),
            },
        )
    )
    assert ix_from_methods == ix_legacy


@mark.asyncio
async def test_at_constructor(program: Program) -> None:
    """Test that the Program.at classmethod works."""
    idl_path = "target/idl/misc.json"
    subprocess.run(
        ["anchor", "idl", "init", "-f", idl_path, str(program.program_id)],
        cwd=PATH,
    )
    fetched = await program.at(program.program_id, program.provider)
    # await fetched.close()
    assert fetched.idl.name == "misc"


@async_fixture(scope="module")
async def initialized_keypair(program: Program) -> Keypair:
    data = Keypair()
    await program.rpc["initialize"](
        1234,
        22,
        ctx=Context(
            accounts={"data": data.pubkey(), "rent": RENT},
            signers=[data],
            pre_instructions=[await program.account["Data"].create_instruction(data)],
        ),
    )
    return data


@mark.asyncio
async def test_readonly_provider(
    program: Program, initialized_keypair: Keypair
) -> None:
    async with Provider.readonly() as provider:
        readonly_program = Program(program.idl, program.program_id, provider=provider)
        data_account = await readonly_program.account["Data"].fetch(
            initialized_keypair.pubkey()
        )
    assert data_account.udata == 1234
    assert data_account.idata == 22


@mark.asyncio
async def test_fetch_multiple(program: Program, initialized_keypair: Keypair) -> None:
    batch_size = 2
    n_accounts = batch_size * 100 + 1
    data_account = await program.account["Data"].fetch(initialized_keypair.pubkey())
    pubkeys = [initialized_keypair.pubkey()] * n_accounts
    data_accounts = await program.account["Data"].fetch_multiple(
        pubkeys, batch_size=batch_size
    )
    assert len(data_accounts) == n_accounts
    assert all(acc == data_account for acc in data_accounts)


@mark.asyncio
async def test_can_use_executable_attribute(program: Program) -> None:
    await program.rpc["test_executable"](
        ctx=Context(accounts={"program": program.program_id}),
    )
    # sleep so we don't get AlreadyProcessed error
    await asyncio.sleep(10)
    with raises(ProgramError):
        await program.rpc["test_executable"](
            ctx=Context(accounts={"program": program.provider.wallet.public_key}),
        )


@mark.asyncio
async def test_can_execute_fallback_function(program: Program) -> None:
    with raises(RPCNoResultException) as excinfo:
        await invoke(program.program_id, program.provider)
    assert (
        "Transaction failed to sanitize accounts offsets correctly"
        in excinfo.value.args[0]
    )


@mark.asyncio
async def test_can_fetch_all_accounts_of_a_given_type(
    program: Program, event_loop
) -> None:
    # Initialize the accounts.
    data1 = Keypair()
    data2 = Keypair()
    data3 = Keypair()
    data4 = Keypair()
    # Initialize filterable data.
    filterable1 = Keypair().pubkey()
    filterable2 = Keypair().pubkey()
    provider = Provider(
        program.provider.connection,
        Wallet(Keypair()),
        program.provider.opts,
    )
    another_program = Program(program.idl, program.program_id, provider)
    lamports_per_sol = 1000000000
    tx_res = await program.provider.connection.request_airdrop(
        another_program.provider.wallet.public_key,
        lamports_per_sol,
    )
    signature = tx_res.value
    await program.provider.connection.confirm_transaction(signature)
    # Create all the accounts.
    tasks = [
        program.rpc["test_fetch_all"](
            filterable1,
            ctx=Context(
                accounts={
                    "data": data1.pubkey(),
                    "authority": program.provider.wallet.public_key,
                    "system_program": SYS_PROGRAM_ID,
                },
                signers=[data1],
            ),
        ),
        program.rpc["test_fetch_all"](
            filterable1,
            ctx=Context(
                accounts={
                    "data": data2.pubkey(),
                    "authority": program.provider.wallet.public_key,
                    "system_program": SYS_PROGRAM_ID,
                },
                signers=[data2],
            ),
        ),
        program.rpc["test_fetch_all"](
            filterable2,
            ctx=Context(
                accounts={
                    "data": data3.pubkey(),
                    "authority": program.provider.wallet.public_key,
                    "system_program": SYS_PROGRAM_ID,
                },
                signers=[data3],
            ),
        ),
        another_program.rpc["test_fetch_all"](
            filterable1,
            ctx=Context(
                accounts={
                    "data": data4.pubkey(),
                    "authority": another_program.provider.wallet.public_key,
                    "system_program": SYS_PROGRAM_ID,
                },
                signers=[data4],
            ),
        ),
    ]
    await asyncio.wait([event_loop.create_task(t) for t in tasks])
    all_accounts = await program.account["DataWithFilter"].all()
    all_accounts_filtered_by_bytes = await program.account["DataWithFilter"].all(
        bytes(program.provider.wallet.public_key),
    )
    all_accounts_filtered_by_program_filters1 = await program.account[
        "DataWithFilter"
    ].all(
        filters=[
            MemcmpOpts(offset=8, bytes=str(program.provider.wallet.public_key)),
            MemcmpOpts(offset=40, bytes=str(filterable1)),
        ],
    )
    all_accounts_filtered_by_program_filters2 = await program.account[
        "DataWithFilter"
    ].all(
        filters=[
            MemcmpOpts(offset=8, bytes=str(program.provider.wallet.public_key)),
            MemcmpOpts(offset=40, bytes=str(filterable2)),
        ],
    )
    assert len(all_accounts) == 4
    assert len(all_accounts_filtered_by_bytes) == 3
    assert len(all_accounts_filtered_by_program_filters1) == 2
    assert len(all_accounts_filtered_by_program_filters2) == 1
