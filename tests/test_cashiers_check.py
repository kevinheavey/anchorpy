"""Mimics anchor/tests/spl/token-proxy."""
from dataclasses import dataclass

from pytest import mark, fixture
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.sysvar import SYSVAR_RENT_PUBKEY
from spl.token.constants import TOKEN_PROGRAM_ID

from anchorpy import Program, Context, Provider
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.utils.token import (
    create_mint_and_vault,
    get_token_account,
    create_token_account,
    create_token_account_instrs,
)
from anchorpy.workspace import WorkspaceType


workspace = workspace_fixture("anchor/tests/cashiers-check")


@dataclass
class InitialState:
    mint: PublicKey
    god: PublicKey
    receiver: PublicKey


@dataclass
class CreatedCheck:
    check: Keypair
    vault: Keypair
    signer: PublicKey
    nonce: int


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    """Create a Program instance."""
    return workspace["cashiers_check"]


@fixture(scope="module")
async def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    return program.provider


@fixture(scope="module")
async def initial_state(provider: Provider) -> InitialState:
    mint, god = await create_mint_and_vault(provider, 1000000)
    receiver = await create_token_account(provider, mint, provider.wallet.public_key)
    return InitialState(mint, god, receiver)


@fixture(scope="module")
async def create_check(program: Program, initial_state: InitialState) -> CreatedCheck:
    check = Keypair()
    vault = Keypair()
    check_signer, nonce = PublicKey.find_program_address(
        [bytes(check.public_key)], program.program_id
    )
    token_account_instrs = await create_token_account_instrs(
        program.provider, vault.public_key, initial_state.mint, check_signer
    )
    accounts = {
        "check": check.public_key,
        "vault": vault.public_key,
        "check_signer": check_signer,
        "from": initial_state.god,
        "to": initial_state.receiver,
        "owner": program.provider.wallet.public_key,
        "token_program": TOKEN_PROGRAM_ID,
        "rent": SYSVAR_RENT_PUBKEY,
    }
    instructions = [
        await program.account["Check"].create_instruction(check, 300),
        *token_account_instrs,
    ]
    await program.rpc["create_check"](
        100,
        "Hello world",
        nonce,
        ctx=Context(
            accounts=accounts, signers=[check, vault], instructions=instructions
        ),
    )
    return CreatedCheck(check, vault, check_signer, nonce)


@mark.asyncio
async def test_create_check(
    program: Program,
    provider: Provider,
    create_check: CreatedCheck,
    initial_state: InitialState,
) -> None:
    check_account = await program.account["Check"].fetch(create_check.check.public_key)
    assert check_account.from_ == initial_state.god
    assert check_account.to == initial_state.receiver
    assert check_account.amount == 100
    assert check_account.memo == "Hello world"
    assert check_account.vault == create_check.vault.public_key
    assert check_account.nonce == create_check.nonce
    assert check_account.burned is False
    vault_account = await get_token_account(provider, check_account.vault)
    assert vault_account.amount == 100


@mark.asyncio
async def test_cash_check(
    program: Program,
    provider: Provider,
    initial_state: InitialState,
    create_check: CreatedCheck,
) -> None:
    await program.rpc["cash_check"](
        ctx=Context(
            accounts={
                "check": create_check.check.public_key,
                "vault": create_check.vault.public_key,
                "check_signer": create_check.signer,
                "to": initial_state.receiver,
                "owner": provider.wallet.public_key,
                "token_program": TOKEN_PROGRAM_ID,
            },
        )
    )
    check_account = await program.account["Check"].fetch(create_check.check.public_key)
    vault_account = await get_token_account(provider, check_account.vault)
    receiver_account = await get_token_account(provider, initial_state.receiver)
    assert check_account.burned is True
    assert vault_account.amount == 0
    assert receiver_account.amount == 100
