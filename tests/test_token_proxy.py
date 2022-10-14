"""Mimics anchor/tests/spl/token-proxy."""
from pytest import mark, fixture
from pytest_asyncio import fixture as async_fixture
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.system_program import create_account, CreateAccountParams
from solana.transaction import TransactionInstruction, Transaction
from spl.token.instructions import (
    initialize_mint,
    InitializeMintParams,
)
from spl.token.constants import TOKEN_PROGRAM_ID

from anchorpy import Program, Context, Provider
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.utils.token import get_mint_info, get_token_account, create_token_account
from anchorpy.workspace import WorkspaceType


workspace = workspace_fixture(
    "anchor/tests/spl/token-proxy/", build_cmd="anchor build --skip-lint"
)


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    """Create a Program instance."""
    return workspace["token_proxy"]


@fixture(scope="module")
def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    return program.provider


async def create_mint_instructions(
    provider: Provider, authority: PublicKey, mint: PublicKey
) -> tuple[TransactionInstruction, TransactionInstruction]:
    mbre_resp = await provider.connection.get_minimum_balance_for_rent_exemption(82)
    lamports = mbre_resp.value
    return (
        create_account(
            CreateAccountParams(
                from_pubkey=provider.wallet.public_key,
                new_account_pubkey=mint,
                space=82,
                lamports=lamports,
                program_id=TOKEN_PROGRAM_ID,
            )
        ),
        initialize_mint(
            InitializeMintParams(
                mint=mint,
                decimals=0,
                mint_authority=authority,
                program_id=TOKEN_PROGRAM_ID,
            )
        ),
    )


async def create_mint(provider: Provider) -> PublicKey:
    authority = provider.wallet.public_key
    mint = Keypair()
    instructions = await create_mint_instructions(provider, authority, mint.public_key)
    tx = Transaction()
    tx.add(*instructions)
    await provider.send(tx, [mint])
    return mint.public_key


@async_fixture(scope="module")
async def created_mint(provider: Provider) -> PublicKey:
    return await create_mint(provider)


@async_fixture(scope="module")
async def from_pubkey(provider: Provider, created_mint: PublicKey) -> PublicKey:
    return await create_token_account(
        provider, created_mint, provider.wallet.public_key
    )


@async_fixture(scope="module")
async def to_pubkey(provider: Provider, created_mint: PublicKey) -> PublicKey:
    return await create_token_account(
        provider, created_mint, provider.wallet.public_key
    )


@async_fixture(scope="module")
async def mint_token(
    program: Program,
    provider: Provider,
    created_mint: PublicKey,
    from_pubkey: PublicKey,
) -> None:
    await program.rpc["proxy_mint_to"](
        1000,
        ctx=Context(
            accounts={
                "authority": provider.wallet.public_key,
                "mint": created_mint,
                "to": from_pubkey,
                "token_program": TOKEN_PROGRAM_ID,
            },
        ),
    )


@mark.asyncio
async def test_mint_token(
    mint_token: None, provider: Provider, from_pubkey: PublicKey
) -> None:
    from_account = await get_token_account(provider, from_pubkey)
    assert from_account.amount == 1000


@async_fixture(scope="module")
async def transfer_token(
    program: Program,
    provider: Provider,
    to_pubkey: PublicKey,
    from_pubkey: PublicKey,
    mint_token: None,
) -> None:
    await program.rpc["proxy_transfer"](
        400,
        ctx=Context(
            accounts={
                "authority": provider.wallet.public_key,
                "to": to_pubkey,
                "from": from_pubkey,
                "token_program": TOKEN_PROGRAM_ID,
            },
        ),
    )


@mark.asyncio
async def test_transfer_token(
    transfer_token: None,
    provider: Provider,
    from_pubkey: PublicKey,
    to_pubkey: PublicKey,
) -> None:
    from_account = await get_token_account(provider, from_pubkey)
    to_account = await get_token_account(provider, to_pubkey)
    assert from_account.amount == 600
    assert to_account.amount == 400


@async_fixture(scope="module")
async def burn_token(
    program: Program,
    provider: Provider,
    to_pubkey: PublicKey,
    created_mint: PublicKey,
    transfer_token: None,
) -> None:
    await program.rpc["proxy_burn"](
        399,
        ctx=Context(
            accounts={
                "authority": provider.wallet.public_key,
                "mint": created_mint,
                "from": to_pubkey,
                "token_program": TOKEN_PROGRAM_ID,
            },
        ),
    )


@mark.asyncio
async def test_burn_token(
    burn_token: None,
    provider: Provider,
    from_pubkey: PublicKey,
    to_pubkey: PublicKey,
) -> None:
    to_account = await get_token_account(provider, to_pubkey)
    assert to_account.amount == 1


@async_fixture(scope="module")
async def set_new_mint_authority(
    program: Program,
    provider: Provider,
    to_pubkey: PublicKey,
    created_mint: PublicKey,
    burn_token: None,
) -> PublicKey:
    new_mint_authority = Keypair()
    authority_type = program.type["AuthorityType"]
    await program.rpc["proxy_set_authority"](
        authority_type.MintTokens(),
        new_mint_authority.public_key,
        ctx=Context(
            accounts={
                "account_or_mint": created_mint,
                "current_authority": provider.wallet.public_key,
                "token_program": TOKEN_PROGRAM_ID,
            },
        ),
    )
    return new_mint_authority.public_key


@mark.asyncio
async def test_set_new_mint_authority(
    set_new_mint_authority: PublicKey,
    created_mint: PublicKey,
    provider: Provider,
    from_pubkey: PublicKey,
    to_pubkey: PublicKey,
) -> None:
    mint_info = await get_mint_info(provider, created_mint)
    assert mint_info.mint_authority == set_new_mint_authority
