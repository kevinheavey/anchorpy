"""Mimics anchor/tests/misc/tests/misc.js."""
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from anchorpy import Context, Program
from anchorpy.error import ProgramError
from anchorpy.program.context import EMPTY_CONTEXT
from anchorpy.program.core import _parse_idl_errors
from anchorpy.program.event import EventParser
from anchorpy.program.namespace.account import AccountClient
from anchorpy.program.namespace.simulate import SimulateResponse
from anchorpy.pytest_plugin import bankrun_fixture
from anchorpy.workspace import WorkspaceType, close_workspace, create_workspace
from pytest import fixture, mark, raises
from pytest_asyncio import fixture as async_fixture
from solana.rpc.core import RPCException
from solders.account import Account
from solders.bankrun import BanksClientError, ProgramTestContext
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.rpc.responses import GetAccountInfoResp, RpcResponseContext
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.system_program import (
    CreateAccountParams,
    TransferParams,
    create_account,
    transfer,
)
from solders.sysvar import RENT
from solders.transaction import TransactionError
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID

PATH = Path("anchor/tests/misc/")
bankrun = bankrun_fixture(PATH, build_cmd="anchor build --skip-lint")


@async_fixture(scope="module")
async def workspace(bankrun: ProgramTestContext) -> AsyncGenerator[WorkspaceType, None]:
    ws = create_workspace(PATH)
    yield ws
    await close_workspace(ws)


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    return workspace["misc"]


@fixture(scope="module")
def misc2program(workspace: WorkspaceType) -> Program:
    return workspace["misc2"]


async def bankrun_rpc(
    prog: Program, name: str, args: list, ctx: Context, bankrun: ProgramTestContext
) -> None:
    recent_blockhash = (await bankrun.banks_client.get_latest_blockhash())[0]
    tx = prog.transaction[name](
        *args, payer=bankrun.payer, blockhash=recent_blockhash, ctx=ctx
    )
    await bankrun.banks_client.process_transaction(tx)


def as_account_info_resp(acc: Optional[Account]) -> GetAccountInfoResp:
    return GetAccountInfoResp(acc, RpcResponseContext(0))


async def bankrun_create_instruction(
    acc: AccountClient, signer: Keypair, program_id: Pubkey, bankrun: ProgramTestContext
) -> Instruction:
    rent = await bankrun.banks_client.get_rent()
    space = acc._size
    mbre = rent.minimum_balance(space)
    return create_account(
        CreateAccountParams(
            from_pubkey=bankrun.payer.pubkey(),
            to_pubkey=signer.pubkey(),
            space=space,
            lamports=mbre,
            owner=program_id,
        )
    )


async def bankrun_fetch(
    acc: AccountClient, address: Pubkey, bankrun: ProgramTestContext
) -> Any:
    raw = await bankrun.banks_client.get_account(address)
    assert raw is not None
    return acc.coder.accounts.decode(raw.data)


async def bankrun_simulate(
    prog: Program, name: str, args: list, ctx: Context, bankrun: ProgramTestContext
) -> SimulateResponse:
    blockhash = (await bankrun.banks_client.get_latest_blockhash())[0]
    tx = prog.transaction[name](
        *args, payer=bankrun.payer, blockhash=blockhash, ctx=ctx
    )
    resp = await bankrun.banks_client.simulate_transaction(tx)
    resp_err = resp.result
    meta = resp.meta
    logs = [] if meta is None else meta.log_messages
    idl_errors = _parse_idl_errors(prog.idl)
    if resp_err is None:
        events = []
        if prog.idl.events is not None:
            parser = EventParser(prog.program_id, prog.coder)
            parser.parse_logs(logs, lambda evt: events.append(evt))
        return SimulateResponse(events, logs)
    else:
        translated_err = ProgramError.parse_tx_error(
            resp_err, idl_errors, prog.program_id, logs
        )
        if translated_err is not None:
            raise translated_err
        raise RPCException(resp_err)


@async_fixture(scope="module")
async def initialized_keypair(program: Program, bankrun: ProgramTestContext) -> Keypair:
    data = Keypair()
    await bankrun_rpc(
        program,
        "initialize",
        [
            1234,
            22,
        ],
        ctx=Context(
            accounts={"data": data.pubkey(), "rent": RENT},
            signers=[data],
            pre_instructions=[
                await bankrun_create_instruction(
                    program.account["Data"], data, program.program_id, bankrun
                )
            ],
        ),
        bankrun=bankrun,
    )
    return data


@mark.asyncio
async def test_can_use_u128_and_i128(
    program: Program, initialized_keypair: Keypair, bankrun: ProgramTestContext
) -> None:
    data_account = await bankrun_fetch(
        program.account["Data"], initialized_keypair.pubkey(), bankrun
    )
    assert data_account.udata == 1234
    assert data_account.idata == 22


@mark.asyncio
async def test_can_use_owner_constraint(
    program: Program, initialized_keypair: Keypair, bankrun: ProgramTestContext
) -> None:
    await bankrun_rpc(
        program,
        "test_owner",
        [],
        ctx=Context(
            accounts={
                "data": initialized_keypair.pubkey(),
                "misc": program.program_id,
            },
        ),
        bankrun=bankrun,
    )
    with raises(TransactionError):
        await bankrun_rpc(
            program,
            "test_owner",
            [],
            ctx=Context(
                accounts={
                    "data": bankrun.payer.pubkey(),
                    "misc": program.program_id,
                },
            ),
            bankrun=bankrun,
        )


@mark.asyncio
async def test_can_retrieve_events_when_simulating_transaction(
    program: Program, bankrun: ProgramTestContext
) -> None:
    resp = await bankrun_simulate(
        program, "test_simulate", [44], ctx=EMPTY_CONTEXT, bankrun=bankrun
    )
    expected_raw_first_entry = (
        "Program 3TEqcc8xhrhdspwbvoamUJe2borm4Nr72JxL66k6rgrh invoke [1]"
    )
    events = resp.events
    assert resp.raw[0] == expected_raw_first_entry
    assert events[0].name == "E1"
    assert events[0].data.data == 44
    assert events[1].name == "E2"
    assert events[1].data.data == 1234
    assert events[2].name == "E3"
    assert events[2].data.data == 9


@mark.asyncio
async def test_fail_to_close_account_when_sending_lamports_to_itself(
    program: Program,
    initialized_keypair: Keypair,
    bankrun: ProgramTestContext,
) -> None:
    with raises(BanksClientError) as excinfo:
        await bankrun_rpc(
            program,
            "test_close",
            [],
            ctx=Context(
                accounts={
                    "data": initialized_keypair.pubkey(),
                    "sol_dest": initialized_keypair.pubkey(),
                },
            ),
            bankrun=bankrun,
        )
    assert "0x7db" in excinfo.value.args[0]


@mark.asyncio
async def test_can_close_account(
    program: Program,
    initialized_keypair: Keypair,
    bankrun: ProgramTestContext,
) -> None:
    client = bankrun.banks_client
    open_account = await client.get_account(initialized_keypair.pubkey())
    assert open_account is not None
    before_balance_res = await client.get_account(
        bankrun.payer.pubkey(),
    )
    assert before_balance_res is not None
    before_balance = before_balance_res.lamports
    await bankrun_rpc(
        program,
        "test_close",
        [],
        ctx=Context(
            accounts={
                "data": initialized_keypair.pubkey(),
                "sol_dest": bankrun.payer.pubkey(),
            },
        ),
        bankrun=bankrun,
    )
    after_balance_res = await client.get_account(
        bankrun.payer.pubkey(),
    )
    assert after_balance_res is not None
    after_balance = after_balance_res.lamports
    assert after_balance > before_balance
    closed_account = await client.get_account(
        initialized_keypair.pubkey(),
    )
    assert closed_account is None


@mark.asyncio
async def test_can_use_instruction_data_in_accounts_constraints(
    program: Program, bankrun: ProgramTestContext
) -> None:
    seed = b"my-seed"
    my_pda, nonce = Pubkey.find_program_address([seed, bytes(RENT)], program.program_id)
    await bankrun_rpc(
        program,
        "test_instruction_constraint",
        [nonce],
        ctx=Context(accounts={"my_pda": my_pda, "my_account": RENT}),
        bankrun=bankrun,
    )


@mark.asyncio
async def test_can_create_a_pda_with_instruction_data(
    program: Program, bankrun: ProgramTestContext
) -> None:
    seed = bytes([1, 2, 3, 4])
    domain = "my-domain"
    foo = RENT
    my_pda, nonce = Pubkey.find_program_address(
        [b"my-seed", domain.encode(), bytes(foo), seed], program.program_id
    )
    await bankrun_rpc(
        program,
        "test_pda_init",
        [domain, seed, nonce],
        ctx=Context(
            accounts={
                "my_pda": my_pda,
                "my_payer": bankrun.payer.pubkey(),
                "foo": foo,
                "rent": RENT,
                "system_program": SYS_PROGRAM_ID,
            }
        ),
        bankrun=bankrun,
    )
    my_pda_account = await bankrun_fetch(program.account["DataU16"], my_pda, bankrun)
    assert my_pda_account.data == 6


@mark.asyncio
async def test_can_create_a_zero_copy_pda(
    program: Program, bankrun: ProgramTestContext
) -> None:
    my_pda, nonce = Pubkey.find_program_address([b"my-seed"], program.program_id)
    await bankrun_rpc(
        program,
        "test_pda_init_zero_copy",
        [],
        ctx=Context(
            accounts={
                "my_pda": my_pda,
                "my_payer": bankrun.payer.pubkey(),
                "rent": RENT,
                "system_program": SYS_PROGRAM_ID,
            },
        ),
        bankrun=bankrun,
    )
    my_pda_account = await bankrun_fetch(
        program.account["DataZeroCopy"], my_pda, bankrun
    )
    assert my_pda_account.data == 9
    assert my_pda_account.bump == nonce


@mark.asyncio
async def test_can_write_to_a_zero_copy_pda(
    program: Program, bankrun: ProgramTestContext
) -> None:
    my_pda, bump = Pubkey.find_program_address([b"my-seed"], program.program_id)
    await bankrun_rpc(
        program,
        "test_pda_mut_zero_copy",
        [],
        ctx=Context(
            accounts={
                "my_pda": my_pda,
                "my_payer": bankrun.payer.pubkey(),
            },
        ),
        bankrun=bankrun,
    )
    my_pda_account = await bankrun_fetch(
        program.account["DataZeroCopy"], my_pda, bankrun
    )
    assert my_pda_account.data == 1234
    assert my_pda_account.bump == bump


@mark.asyncio
async def test_can_create_a_token_account_from_seeds_pda(
    program: Program, bankrun: ProgramTestContext
) -> None:
    mint, mint_bump = Pubkey.find_program_address([b"my-mint-seed"], program.program_id)
    my_pda, token_bump = Pubkey.find_program_address(
        [b"my-token-seed"], program.program_id
    )
    await bankrun_rpc(
        program,
        "test_token_seeds_init",
        [],
        ctx=Context(
            accounts={
                "my_pda": my_pda,
                "mint": mint,
                "authority": bankrun.payer.pubkey(),
                "system_program": SYS_PROGRAM_ID,
                "rent": RENT,
                "token_program": TOKEN_PROGRAM_ID,
            },
        ),
        bankrun=bankrun,
    )
    mint_account = AsyncToken(
        program.provider.connection, mint, TOKEN_PROGRAM_ID, bankrun.payer
    )
    account_raw = await bankrun.banks_client.get_account(my_pda)
    as_acc_info = as_account_info_resp(account_raw)
    account = mint_account._create_account_info(as_acc_info)
    assert account.is_frozen is False
    assert account.is_initialized is True
    assert account.amount == 0
    assert account.owner == bankrun.payer.pubkey()
    assert account.mint == mint


@mark.asyncio
async def test_can_init_random_account(
    program: Program, bankrun: ProgramTestContext
) -> None:
    data = Keypair()
    await bankrun_rpc(
        program,
        "test_init",
        [],
        ctx=Context(
            accounts={
                "data": data.pubkey(),
                "payer": bankrun.payer.pubkey(),
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[data],
        ),
        bankrun=bankrun,
    )
    account = await bankrun_fetch(program.account["DataI8"], data.pubkey(), bankrun)
    assert account.data == 3


@mark.asyncio
async def test_can_init_random_account_prefunded(
    program: Program, bankrun: ProgramTestContext
) -> None:
    data = Keypair()
    await bankrun_rpc(
        program,
        "test_init",
        [],
        ctx=Context(
            accounts={
                "data": data.pubkey(),
                "payer": bankrun.payer.pubkey(),
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[data],
            pre_instructions=[
                transfer(
                    TransferParams(
                        from_pubkey=bankrun.payer.pubkey(),
                        to_pubkey=data.pubkey(),
                        lamports=4039280,
                    ),
                ),
            ],
        ),
        bankrun=bankrun,
    )
    account = await bankrun_fetch(program.account["DataI8"], data.pubkey(), bankrun)
    assert account.data == 3


@mark.asyncio
async def test_can_init_random_zero_copy_account(
    program: Program, bankrun: ProgramTestContext
) -> None:
    data = Keypair()
    await bankrun_rpc(
        program,
        "test_init_zero_copy",
        [],
        ctx=Context(
            accounts={
                "data": data.pubkey(),
                "payer": bankrun.payer.pubkey(),
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[data],
        ),
        bankrun=bankrun,
    )
    account = await bankrun_fetch(
        program.account["DataZeroCopy"], data.pubkey(), bankrun
    )
    assert account.data == 10
    assert account.bump == 2


@mark.asyncio
async def test_can_create_random_mint_account(
    program: Program, bankrun: ProgramTestContext
) -> None:
    mint = Keypair()
    await bankrun_rpc(
        program,
        "test_init_mint",
        [],
        ctx=Context(
            accounts={
                "mint": mint.pubkey(),
                "payer": bankrun.payer.pubkey(),
                "system_program": SYS_PROGRAM_ID,
                "token_program": TOKEN_PROGRAM_ID,
                "rent": RENT,
            },
            signers=[mint],
        ),
        bankrun=bankrun,
    )
    client = AsyncToken(
        program.provider.connection,
        mint.pubkey(),
        TOKEN_PROGRAM_ID,
        bankrun.payer,
    )
    mint_acc_raw = await bankrun.banks_client.get_account(client.pubkey)
    mint_account = client._create_mint_info(as_account_info_resp(mint_acc_raw))
    assert mint_account.decimals == 6
    assert mint_account.mint_authority == bankrun.payer.pubkey()
    assert mint_account.freeze_authority == bankrun.payer.pubkey()


@async_fixture(scope="module")
async def prefunded_mint(program: Program, bankrun: ProgramTestContext) -> Keypair:
    mint = Keypair()
    await bankrun_rpc(
        program,
        "test_init_mint",
        [],
        ctx=Context(
            accounts={
                "mint": mint.pubkey(),
                "payer": bankrun.payer.pubkey(),
                "system_program": SYS_PROGRAM_ID,
                "token_program": TOKEN_PROGRAM_ID,
                "rent": RENT,
            },
            signers=[mint],
            pre_instructions=[
                transfer(
                    TransferParams(
                        from_pubkey=bankrun.payer.pubkey(),
                        to_pubkey=mint.pubkey(),
                        lamports=4039280,
                    ),
                ),
            ],
        ),
        bankrun=bankrun,
    )
    return mint


@mark.asyncio
async def test_can_create_random_mint_account_prefunded(
    program: Program,
    prefunded_mint: Keypair,
    bankrun: ProgramTestContext,
) -> None:
    client = AsyncToken(
        program.provider.connection,
        prefunded_mint.pubkey(),
        TOKEN_PROGRAM_ID,
        bankrun.payer,
    )
    mint_acc_raw = await bankrun.banks_client.get_account(client.pubkey)
    mint_account = client._create_mint_info(as_account_info_resp(mint_acc_raw))
    assert mint_account.decimals == 6
    assert mint_account.mint_authority == bankrun.payer.pubkey()


@mark.asyncio
async def test_can_create_random_token_account(
    program: Program,
    prefunded_mint: Keypair,
    bankrun: ProgramTestContext,
) -> None:
    token = Keypair()
    await bankrun_rpc(
        program,
        "test_init_token",
        [],
        ctx=Context(
            accounts={
                "token": token.pubkey(),
                "mint": prefunded_mint.pubkey(),
                "payer": bankrun.payer.pubkey(),
                "system_program": SYS_PROGRAM_ID,
                "token_program": TOKEN_PROGRAM_ID,
                "rent": RENT,
            },
            signers=[token],
        ),
        bankrun=bankrun,
    )
    client = AsyncToken(
        program.provider.connection,
        prefunded_mint.pubkey(),
        TOKEN_PROGRAM_ID,
        bankrun.payer,
    )
    account_raw = await bankrun.banks_client.get_account(token.pubkey())
    account = client._create_account_info(as_account_info_resp(account_raw))
    assert not account.is_frozen
    assert account.amount == 0
    assert account.is_initialized
    assert account.owner == bankrun.payer.pubkey()
    assert account.mint == prefunded_mint.pubkey()


@mark.asyncio
async def test_can_create_random_token_account_with_prefunding(
    program: Program,
    prefunded_mint: Keypair,
    bankrun: ProgramTestContext,
) -> None:
    token = Keypair()
    await bankrun_rpc(
        program,
        "test_init_token",
        [],
        ctx=Context(
            accounts={
                "token": token.pubkey(),
                "mint": prefunded_mint.pubkey(),
                "payer": bankrun.payer.pubkey(),
                "system_program": SYS_PROGRAM_ID,
                "token_program": TOKEN_PROGRAM_ID,
                "rent": RENT,
            },
            signers=[token],
            pre_instructions=[
                transfer(
                    TransferParams(
                        from_pubkey=bankrun.payer.pubkey(),
                        to_pubkey=token.pubkey(),
                        lamports=4039280,
                    ),
                )
            ],
        ),
        bankrun=bankrun,
    )
    client = AsyncToken(
        program.provider.connection,
        prefunded_mint.pubkey(),
        TOKEN_PROGRAM_ID,
        bankrun.payer,
    )
    account_raw = await bankrun.banks_client.get_account(token.pubkey())
    account = client._create_account_info(as_account_info_resp(account_raw))
    assert not account.is_frozen
    assert account.amount == 0
    assert account.is_initialized
    assert account.owner == bankrun.payer.pubkey()
    assert account.mint == prefunded_mint.pubkey()


@mark.asyncio
async def test_can_create_random_token_account_with_prefunding_under_rent_exemption(
    program: Program,
    prefunded_mint: Keypair,
    bankrun: ProgramTestContext,
) -> None:
    token = Keypair()
    await bankrun_rpc(
        program,
        "test_init_token",
        [],
        ctx=Context(
            accounts={
                "token": token.pubkey(),
                "mint": prefunded_mint.pubkey(),
                "payer": bankrun.payer.pubkey(),
                "system_program": SYS_PROGRAM_ID,
                "token_program": TOKEN_PROGRAM_ID,
                "rent": RENT,
            },
            signers=[token],
            pre_instructions=[
                transfer(
                    TransferParams(
                        from_pubkey=bankrun.payer.pubkey(),
                        to_pubkey=token.pubkey(),
                        lamports=1,
                    ),
                )
            ],
        ),
        bankrun=bankrun,
    )
    client = AsyncToken(
        program.provider.connection,
        prefunded_mint.pubkey(),
        TOKEN_PROGRAM_ID,
        bankrun.payer,
    )
    account_raw = await bankrun.banks_client.get_account(token.pubkey())
    account = client._create_account_info(as_account_info_resp(account_raw))
    assert not account.is_frozen
    assert account.amount == 0
    assert account.is_initialized
    assert account.owner == bankrun.payer.pubkey()
    assert account.mint == prefunded_mint.pubkey()


@mark.asyncio
async def test_init_multiple_accounts_via_composite_payer(
    program: Program, bankrun: ProgramTestContext
) -> None:
    data1 = Keypair()
    data2 = Keypair()
    await bankrun_rpc(
        program,
        "test_composite_payer",
        [],
        ctx=Context(
            accounts={
                "composite": {
                    "data": data1.pubkey(),
                    "payer": bankrun.payer.pubkey(),
                    "system_program": SYS_PROGRAM_ID,
                },
                "data": data2.pubkey(),
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[data1, data2],
        ),
        bankrun=bankrun,
    )
    account1 = await bankrun_fetch(program.account["DataI8"], data1.pubkey(), bankrun)
    assert account1.data == 1

    account2 = await bankrun_fetch(program.account["Data"], data2.pubkey(), bankrun)
    assert account2.udata == 2
    assert account2.idata == 3


@mark.asyncio
async def test_can_create_associated_token_account(
    program: Program, bankrun: ProgramTestContext
) -> None:
    # TODO
    pass


@mark.asyncio
async def test_can_validate_associated_token_constraints(
    program: Program, bankrun: ProgramTestContext
) -> None:
    # TODO
    pass


@mark.asyncio
async def test_can_use_pdas_with_empty_seeds(
    program: Program, bankrun: ProgramTestContext
) -> None:
    pda, bump = Pubkey.find_program_address([], program.program_id)
    await bankrun_rpc(
        program,
        "test_init_with_empty_seeds",
        [],
        ctx=Context(
            accounts={
                "pda": pda,
                "authority": bankrun.payer.pubkey(),
                "system_program": SYS_PROGRAM_ID,
            },
        ),
        bankrun=bankrun,
    )
    await bankrun_rpc(
        program,
        "test_empty_seeds_constraint",
        [],
        ctx=Context(
            accounts={
                "pda": pda,
            },
        ),
        bankrun=bankrun,
    )
    pda2, _ = Pubkey.find_program_address(
        [b"non-empty"],
        program.program_id,
    )
    with raises(BanksClientError) as excinfo:
        await bankrun_rpc(
            program,
            "test_empty_seeds_constraint",
            [],
            ctx=Context(
                accounts={
                    "pda": pda2,
                },
            ),
            bankrun=bankrun,
        )
    assert "0x7d6" in excinfo.value.args[0]


@async_fixture(scope="module")
async def if_needed_acc(program: Program, bankrun: ProgramTestContext) -> Keypair:
    keypair = Keypair()
    await bankrun_rpc(
        program,
        "test_init_if_needed",
        [1],
        ctx=Context(
            accounts={
                "data": keypair.pubkey(),
                "system_program": SYS_PROGRAM_ID,
                "payer": bankrun.payer.pubkey(),
            },
            signers=[keypair],
        ),
        bankrun=bankrun,
    )
    return keypair


@mark.asyncio
async def test_can_init_if_needed_a_new_account(
    program: Program,
    if_needed_acc: Keypair,
    bankrun: ProgramTestContext,
) -> None:
    account = await bankrun_fetch(
        program.account["DataU16"], if_needed_acc.pubkey(), bankrun
    )
    assert account.data == 1


@mark.asyncio
async def test_can_init_if_needed_a_previously_created_account(
    program: Program,
    if_needed_acc: Keypair,
    bankrun: ProgramTestContext,
) -> None:
    await bankrun_rpc(
        program,
        "test_init_if_needed",
        [3],
        ctx=Context(
            accounts={
                "data": if_needed_acc.pubkey(),
                "system_program": SYS_PROGRAM_ID,
                "payer": bankrun.payer.pubkey(),
            },
            signers=[if_needed_acc],
        ),
        bankrun=bankrun,
    )
    account = await bankrun_fetch(
        program.account["DataU16"], if_needed_acc.pubkey(), bankrun
    )
    assert account.data == 3
