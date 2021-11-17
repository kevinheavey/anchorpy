"""Mimics anchor/tests/spl/token-proxy."""
from pathlib import Path
from typing import AsyncGenerator

from pytest import mark, fixture
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.system_program import create_account, CreateAccountParams
from solana.transaction import TransactionInstruction, Transaction
from spl.token.instructions import (
    initialize_mint,
    InitializeMintParams,
)
from spl.token.constants import TOKEN_PROGRAM_ID

from anchorpy import Program, create_workspace, close_workspace, Context, Provider
from anchorpy.pytest_plugin import get_localnet
from anchorpy.utils.token import get_mint_info, get_token_account, create_token_account

PATH = Path("anchor/tests/spl/token-proxy/")

localnet = get_localnet(PATH)


@fixture(scope="module")
async def program(localnet) -> AsyncGenerator[Program, None]:
    """Create a Program instance."""
    workspace = create_workspace(PATH)
    yield workspace["token_proxy"]
    await close_workspace(workspace)


@fixture(scope="module")
async def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    return program.provider


async def create_mint_instructions(
    provider: Provider, authority: PublicKey, mint: PublicKey
) -> tuple[TransactionInstruction, TransactionInstruction]:
    mbre_resp = await provider.connection.get_minimum_balance_for_rent_exemption(82)
    lamports = mbre_resp["result"]
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


@fixture(scope="module")
async def created_mint(provider: Provider) -> PublicKey:
    return await create_mint(provider)


@fixture(scope="module")
async def from_pubkey(provider: Provider, created_mint: PublicKey) -> PublicKey:
    return await create_token_account(
        provider, created_mint, provider.wallet.public_key
    )


@fixture(scope="module")
async def to_pubkey(provider: Provider, created_mint: PublicKey) -> PublicKey:
    return await create_token_account(
        provider, created_mint, provider.wallet.public_key
    )


@fixture(scope="module")
async def mint_token(
    program: Program,
    provider: Provider,
    created_mint: PublicKey,
    from_pubkey: PublicKey,
) -> None:
    await program.rpc["proxyMintTo"](
        1000,
        ctx=Context(
            accounts={
                "authority": provider.wallet.public_key,
                "mint": created_mint,
                "to": from_pubkey,
                "tokenProgram": TOKEN_PROGRAM_ID,
            },
        ),
    )


@mark.asyncio
async def test_mint_token(
    mint_token: None, provider: Provider, from_pubkey: PublicKey
) -> None:
    from_account = await get_token_account(provider, from_pubkey)
    assert from_account.amount == 1000


@fixture(scope="module")
async def transfer_token(
    program: Program,
    provider: Provider,
    to_pubkey: PublicKey,
    from_pubkey: PublicKey,
    mint_token: None,
) -> None:
    await program.rpc["proxyTransfer"](
        400,
        ctx=Context(
            accounts={
                "authority": provider.wallet.public_key,
                "to": to_pubkey,
                "from": from_pubkey,
                "tokenProgram": TOKEN_PROGRAM_ID,
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


@fixture(scope="module")
async def burn_token(
    program: Program,
    provider: Provider,
    to_pubkey: PublicKey,
    created_mint: PublicKey,
    transfer_token: None,
) -> None:
    await program.rpc["proxyBurn"](
        399,
        ctx=Context(
            accounts={
                "authority": provider.wallet.public_key,
                "mint": created_mint,
                "to": to_pubkey,
                "tokenProgram": TOKEN_PROGRAM_ID,
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


@fixture(scope="module")
async def set_new_mint_authority(
    program: Program,
    provider: Provider,
    to_pubkey: PublicKey,
    created_mint: PublicKey,
    burn_token: None,
) -> PublicKey:
    new_mint_authority = Keypair()
    authority_type = program.type["AuthorityType"]
    await program.rpc["proxySetAuthority"](
        authority_type.MintTokens(),
        new_mint_authority.public_key,
        ctx=Context(
            accounts={
                "accountOrMint": created_mint,
                "currentAuthority": provider.wallet.public_key,
                "tokenProgram": TOKEN_PROGRAM_ID,
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
