"""Mimics anchor/tests/misc/tests/misc.js."""
from pathlib import Path

from anchorpy import Context, Program
from anchorpy.error import ProgramError
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType
from pytest import fixture, mark, raises
from pytest_asyncio import fixture as async_fixture
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.system_program import TransferParams, transfer
from solders.sysvar import RENT
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID

PATH = Path("anchor/tests/misc/")
workspace = workspace_fixture(PATH, build_cmd="anchor build --skip-lint")


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    return workspace["misc"]


@fixture(scope="module")
def misc2program(workspace: WorkspaceType) -> Program:
    return workspace["misc2"]


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
async def test_can_use_u128_and_i128(
    program: Program, initialized_keypair: Keypair
) -> None:
    data_account = await program.account["Data"].fetch(initialized_keypair.pubkey())
    assert data_account.udata == 1234
    assert data_account.idata == 22


@mark.asyncio
async def test_can_use_owner_constraint(
    program: Program, initialized_keypair: Keypair
) -> None:
    await program.rpc["test_owner"](
        ctx=Context(
            accounts={
                "data": initialized_keypair.pubkey(),
                "misc": program.program_id,
            },
        ),
    )
    with raises(ProgramError):
        await program.rpc["test_owner"](
            ctx=Context(
                accounts={
                    "data": program.provider.wallet.public_key,
                    "misc": program.program_id,
                },
            ),
        )


@mark.asyncio
async def test_can_retrieve_events_when_simulating_transaction(
    program: Program,
) -> None:
    resp = await program.simulate["test_simulate"](44)
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
) -> None:
    with raises(ProgramError) as excinfo:
        await program.rpc["test_close"](
            ctx=Context(
                accounts={
                    "data": initialized_keypair.pubkey(),
                    "sol_dest": initialized_keypair.pubkey(),
                },
            ),
        )
    assert excinfo.value.code == 2011
    assert excinfo.value.msg == "A close constraint was violated"


@mark.asyncio
async def test_can_close_account(
    program: Program,
    initialized_keypair: Keypair,
) -> None:
    open_account = await program.provider.connection.get_account_info(
        initialized_keypair.pubkey(),
    )
    assert open_account.value is not None
    before_balance_raw = await program.provider.connection.get_account_info(
        program.provider.wallet.public_key,
    )
    before_balance_res = before_balance_raw.value
    assert before_balance_res is not None
    before_balance = before_balance_res.lamports
    await program.rpc["test_close"](
        ctx=Context(
            accounts={
                "data": initialized_keypair.pubkey(),
                "sol_dest": program.provider.wallet.public_key,
            },
        ),
    )
    after_balance_raw = await program.provider.connection.get_account_info(
        program.provider.wallet.public_key,
    )
    after_balance_res = after_balance_raw.value
    assert after_balance_res is not None
    after_balance = after_balance_res.lamports
    assert after_balance > before_balance
    closed_account = await program.provider.connection.get_account_info(
        initialized_keypair.pubkey(),
    )
    assert closed_account.value is None


@mark.asyncio
async def test_can_use_instruction_data_in_accounts_constraints(
    program: Program,
) -> None:
    seed = b"my-seed"
    my_pda, nonce = Pubkey.find_program_address([seed, bytes(RENT)], program.program_id)
    await program.rpc["test_instruction_constraint"](
        nonce,
        ctx=Context(accounts={"my_pda": my_pda, "my_account": RENT}),
    )


@mark.asyncio
async def test_can_create_a_pda_with_instruction_data(
    program: Program,
) -> None:
    seed = bytes([1, 2, 3, 4])
    domain = "my-domain"
    foo = RENT
    my_pda, nonce = Pubkey.find_program_address(
        [b"my-seed", domain.encode(), bytes(foo), seed], program.program_id
    )
    await program.rpc["test_pda_init"](
        domain,
        seed,
        nonce,
        ctx=Context(
            accounts={
                "my_pda": my_pda,
                "my_payer": program.provider.wallet.public_key,
                "foo": foo,
                "rent": RENT,
                "system_program": SYS_PROGRAM_ID,
            }
        ),
    )
    my_pda_account = await program.account["DataU16"].fetch(my_pda)
    assert my_pda_account.data == 6


@mark.asyncio
async def test_can_create_a_zero_copy_pda(program: Program) -> None:
    my_pda, nonce = Pubkey.find_program_address([b"my-seed"], program.program_id)
    await program.rpc["test_pda_init_zero_copy"](
        ctx=Context(
            accounts={
                "my_pda": my_pda,
                "my_payer": program.provider.wallet.public_key,
                "rent": RENT,
                "system_program": SYS_PROGRAM_ID,
            },
        ),
    )
    my_pda_account = await program.account["DataZeroCopy"].fetch(my_pda)
    assert my_pda_account.data == 9
    assert my_pda_account.bump == nonce


@mark.asyncio
async def test_can_write_to_a_zero_copy_pda(program: Program) -> None:
    my_pda, bump = Pubkey.find_program_address([b"my-seed"], program.program_id)
    await program.rpc["test_pda_mut_zero_copy"](
        ctx=Context(
            accounts={
                "my_pda": my_pda,
                "my_payer": program.provider.wallet.public_key,
            },
        )
    )
    my_pda_account = await program.account["DataZeroCopy"].fetch(my_pda)
    assert my_pda_account.data == 1234
    assert my_pda_account.bump == bump


@mark.asyncio
async def test_can_create_a_token_account_from_seeds_pda(program: Program) -> None:
    mint, mint_bump = Pubkey.find_program_address([b"my-mint-seed"], program.program_id)
    my_pda, token_bump = Pubkey.find_program_address(
        [b"my-token-seed"], program.program_id
    )
    await program.rpc["test_token_seeds_init"](
        ctx=Context(
            accounts={
                "my_pda": my_pda,
                "mint": mint,
                "authority": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
                "rent": RENT,
                "token_program": TOKEN_PROGRAM_ID,
            },
        ),
    )
    mint_account = AsyncToken(
        program.provider.connection,
        mint,
        TOKEN_PROGRAM_ID,
        program.provider.wallet.payer,
    )
    account = await mint_account.get_account_info(my_pda)
    assert account.is_frozen is False
    assert account.is_initialized is True
    assert account.amount == 0
    assert account.owner == program.provider.wallet.public_key
    assert account.mint == mint


@mark.asyncio
async def test_can_init_random_account(program: Program) -> None:
    data = Keypair()
    await program.rpc["test_init"](
        ctx=Context(
            accounts={
                "data": data.pubkey(),
                "payer": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[data],
        ),
    )
    account = await program.account["DataI8"].fetch(data.pubkey())
    assert account.data == 3


@mark.asyncio
async def test_can_init_random_account_prefunded(program: Program) -> None:
    data = Keypair()
    await program.rpc["test_init"](
        ctx=Context(
            accounts={
                "data": data.pubkey(),
                "payer": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[data],
            pre_instructions=[
                transfer(
                    TransferParams(
                        from_pubkey=program.provider.wallet.public_key,
                        to_pubkey=data.pubkey(),
                        lamports=4039280,
                    ),
                ),
            ],
        ),
    )
    account = await program.account["DataI8"].fetch(data.pubkey())
    assert account.data == 3


@mark.asyncio
async def test_can_init_random_zero_copy_account(program: Program) -> None:
    data = Keypair()
    await program.rpc["test_init_zero_copy"](
        ctx=Context(
            accounts={
                "data": data.pubkey(),
                "payer": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[data],
        ),
    )
    account = await program.account["DataZeroCopy"].fetch(data.pubkey())
    assert account.data == 10
    assert account.bump == 2


@mark.asyncio
async def test_can_create_random_mint_account(
    program: Program,
) -> None:
    mint = Keypair()
    await program.rpc["test_init_mint"](
        ctx=Context(
            accounts={
                "mint": mint.pubkey(),
                "payer": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
                "token_program": TOKEN_PROGRAM_ID,
                "rent": RENT,
            },
            signers=[mint],
        ),
    )
    client = AsyncToken(
        program.provider.connection,
        mint.pubkey(),
        TOKEN_PROGRAM_ID,
        program.provider.wallet.payer,
    )
    mint_account = await client.get_mint_info()
    assert mint_account.decimals == 6
    assert mint_account.mint_authority == program.provider.wallet.public_key
    assert mint_account.freeze_authority == program.provider.wallet.public_key


@async_fixture(scope="module")
async def prefunded_mint(program: Program) -> Keypair:
    mint = Keypair()
    await program.rpc["test_init_mint"](
        ctx=Context(
            accounts={
                "mint": mint.pubkey(),
                "payer": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
                "token_program": TOKEN_PROGRAM_ID,
                "rent": RENT,
            },
            signers=[mint],
            pre_instructions=[
                transfer(
                    TransferParams(
                        from_pubkey=program.provider.wallet.public_key,
                        to_pubkey=mint.pubkey(),
                        lamports=4039280,
                    ),
                ),
            ],
        ),
    )
    return mint


@mark.asyncio
async def test_can_create_random_mint_account_prefunded(
    program: Program,
    prefunded_mint: Keypair,
) -> None:
    client = AsyncToken(
        program.provider.connection,
        prefunded_mint.pubkey(),
        TOKEN_PROGRAM_ID,
        program.provider.wallet.payer,
    )
    mint_account = await client.get_mint_info()
    assert mint_account.decimals == 6
    assert mint_account.mint_authority == program.provider.wallet.public_key


@mark.asyncio
async def test_can_create_random_token_account(
    program: Program,
    prefunded_mint: Keypair,
) -> None:
    token = Keypair()
    await program.rpc["test_init_token"](
        ctx=Context(
            accounts={
                "token": token.pubkey(),
                "mint": prefunded_mint.pubkey(),
                "payer": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
                "token_program": TOKEN_PROGRAM_ID,
                "rent": RENT,
            },
            signers=[token],
        ),
    )
    client = AsyncToken(
        program.provider.connection,
        prefunded_mint.pubkey(),
        TOKEN_PROGRAM_ID,
        program.provider.wallet.payer,
    )
    account = await client.get_account_info(token.pubkey())
    assert not account.is_frozen
    assert account.amount == 0
    assert account.is_initialized
    assert account.owner == program.provider.wallet.public_key
    assert account.mint == prefunded_mint.pubkey()


@mark.asyncio
async def test_can_create_random_token_account_with_prefunding(
    program: Program,
    prefunded_mint: Keypair,
) -> None:
    token = Keypair()
    await program.rpc["test_init_token"](
        ctx=Context(
            accounts={
                "token": token.pubkey(),
                "mint": prefunded_mint.pubkey(),
                "payer": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
                "token_program": TOKEN_PROGRAM_ID,
                "rent": RENT,
            },
            signers=[token],
            pre_instructions=[
                transfer(
                    TransferParams(
                        from_pubkey=program.provider.wallet.public_key,
                        to_pubkey=token.pubkey(),
                        lamports=4039280,
                    ),
                )
            ],
        ),
    )
    client = AsyncToken(
        program.provider.connection,
        prefunded_mint.pubkey(),
        TOKEN_PROGRAM_ID,
        program.provider.wallet.payer,
    )
    account = await client.get_account_info(token.pubkey())
    assert not account.is_frozen
    assert account.amount == 0
    assert account.is_initialized
    assert account.owner == program.provider.wallet.public_key
    assert account.mint == prefunded_mint.pubkey()


@mark.asyncio
async def test_can_create_random_token_account_with_prefunding_under_rent_exemption(
    program: Program,
    prefunded_mint: Keypair,
) -> None:
    token = Keypair()
    await program.rpc["test_init_token"](
        ctx=Context(
            accounts={
                "token": token.pubkey(),
                "mint": prefunded_mint.pubkey(),
                "payer": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
                "token_program": TOKEN_PROGRAM_ID,
                "rent": RENT,
            },
            signers=[token],
            pre_instructions=[
                transfer(
                    TransferParams(
                        from_pubkey=program.provider.wallet.public_key,
                        to_pubkey=token.pubkey(),
                        lamports=1,
                    ),
                )
            ],
        ),
    )
    client = AsyncToken(
        program.provider.connection,
        prefunded_mint.pubkey(),
        TOKEN_PROGRAM_ID,
        program.provider.wallet.payer,
    )
    account = await client.get_account_info(token.pubkey())
    assert not account.is_frozen
    assert account.amount == 0
    assert account.is_initialized
    assert account.owner == program.provider.wallet.public_key
    assert account.mint == prefunded_mint.pubkey()


@mark.asyncio
async def test_init_multiple_accounts_via_composite_payer(program: Program) -> None:
    data1 = Keypair()
    data2 = Keypair()
    await program.rpc["test_composite_payer"](
        ctx=Context(
            accounts={
                "composite": {
                    "data": data1.pubkey(),
                    "payer": program.provider.wallet.public_key,
                    "system_program": SYS_PROGRAM_ID,
                },
                "data": data2.pubkey(),
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[data1, data2],
        )
    )
    account1 = await program.account["DataI8"].fetch(data1.pubkey())
    assert account1.data == 1

    account2 = await program.account["Data"].fetch(data2.pubkey())
    assert account2.udata == 2
    assert account2.idata == 3


@mark.asyncio
async def test_can_create_associated_token_account(program: Program) -> None:
    # TODO
    pass


@mark.asyncio
async def test_can_validate_associated_token_constraints(program: Program) -> None:
    # TODO
    pass


@mark.asyncio
async def test_can_use_pdas_with_empty_seeds(program: Program) -> None:
    pda, bump = Pubkey.find_program_address([], program.program_id)
    await program.rpc["test_init_with_empty_seeds"](
        ctx=Context(
            accounts={
                "pda": pda,
                "authority": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
            },
        ),
    )
    await program.rpc["test_empty_seeds_constraint"](
        ctx=Context(
            accounts={
                "pda": pda,
            },
        ),
    )
    pda2, _ = Pubkey.find_program_address(
        [b"non-empty"],
        program.program_id,
    )
    with raises(ProgramError) as excinfo:
        await program.rpc["test_empty_seeds_constraint"](
            ctx=Context(
                accounts={
                    "pda": pda2,
                },
            ),
        )
    assert excinfo.value.code == 2006


@async_fixture(scope="module")
async def if_needed_acc(program: Program) -> Keypair:
    keypair = Keypair()
    await program.rpc["test_init_if_needed"](
        1,
        ctx=Context(
            accounts={
                "data": keypair.pubkey(),
                "system_program": SYS_PROGRAM_ID,
                "payer": program.provider.wallet.public_key,
            },
            signers=[keypair],
        ),
    )
    return keypair


@mark.asyncio
async def test_can_init_if_needed_a_new_account(
    program: Program,
    if_needed_acc: Keypair,
) -> None:
    account = await program.account["DataU16"].fetch(if_needed_acc.pubkey())
    assert account.data == 1


@mark.asyncio
async def test_can_init_if_needed_a_previously_created_account(
    program: Program,
    if_needed_acc: Keypair,
) -> None:
    await program.rpc["test_init_if_needed"](
        3,
        ctx=Context(
            accounts={
                "data": if_needed_acc.pubkey(),
                "system_program": SYS_PROGRAM_ID,
                "payer": program.provider.wallet.public_key,
            },
            signers=[if_needed_acc],
        ),
    )
    account = await program.account["DataU16"].fetch(if_needed_acc.pubkey())
    assert account.data == 3
