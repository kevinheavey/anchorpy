"""Mimics anchor/tests/escrow/tests/escrow.js."""
import asyncio
from pathlib import Path
from typing import AsyncGenerator

from solana.keypair import Keypair
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID

from pytest import fixture, mark
from anchorpy import Program, Provider, create_workspace, close_workspace
from tests.utils import get_localnet

PATH = Path("anchor/tests/escrow")

localnet = get_localnet(PATH)


@fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@fixture(scope="module")
async def program(localnet) -> AsyncGenerator[Program, None]:
    """Create a Program instance."""
    workspace = create_workspace(PATH)
    yield workspace["escrow"]
    await close_workspace(workspace)


@fixture(scope="module")
async def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    return program.provider


@fixture(scope="module")
async def initialize_escrow(program: Program, provider: Provider):
    taker_amount = 1000
    initializer_amount = 500
    escrow_account = Keypair.generate()
    payer = Keypair()
    mint_authority = Keypair()
    await provider.client.request_airdrop(payer.public_key, 10000000000)
    mint_a = await AsyncToken.create_mint(
        provider.client,
        payer,
        mint_authority.public_key,
        0,
        TOKEN_PROGRAM_ID,
        None,
    )

    initializer_token_account_a = await mint_a.create_account(
        provider.wallet.public_key,
    )
    taker_token_account_a = await mint_a.create_account(provider.wallet.public_key)
    await mint_a.mint_to(
        initializer_token_account_a,
        mint_authority.public_key,
        initializer_amount,
        [mint_authority],
    )
    mint_b = await AsyncToken.create_mint(
        provider.client, payer, mint_authority.public_key, 0, TOKEN_PROGRAM_ID, None
    )

    initializer_token_account_b = await mint_b.create_account(
        provider.wallet.public_key
    )
    taker_token_account_b = await mint_b.create_account(provider.wallet.public_key)

    await mint_b.mint_to(
        taker_token_account_b,
        mint_authority.public_key,
        taker_amount,
        [mint_authority],
    )
    return (
        mint_a,
        mint_b,
        initializer_token_account_a,
        initializer_token_account_b,
        taker_token_account_a,
        taker_token_account_b,
    )


# @mark.asyncio
# async def test_initialized_escrow_state(initialize_escrow):
#     (
#         mint_a,
#         mint_b,
#         initializer_token_account_a,
#         initializer_token_account_b,
#         taker_token_account_a,
#         taker_token_account_b,
#     ) = initialize_escrow
#     _initializer_token_account_a = await mint_a.get_account_info(
#         initializer_token_account_a
#     )
#     _taker_token_account_b = await mint_b.get_account_info(taker_token_account_b)
#     print(_initializer_token_account_a)
