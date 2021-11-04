import asyncio
from pathlib import Path
from typing import Tuple

from pytest import mark, fixture
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.sysvar import SYSVAR_RENT_PUBKEY
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID

from anchorpy import Program, create_workspace, Context, Provider
from anchorpy.pytest_plugin import get_localnet

PATH = Path("anchor/tests/composite/")

localnet = get_localnet(PATH)


async def create_mint(prov: Provider) -> AsyncToken:
    authority = prov.wallet.public_key
    return await AsyncToken.create_mint(
        prov.client, prov.wallet.payer, authority, 6, TOKEN_PROGRAM_ID
    )


async def create_token_account(
    prov: Provider,
    mint: PublicKey,
    owner: PublicKey,
) -> PublicKey:
    token = AsyncToken(prov.client, mint, TOKEN_PROGRAM_ID, prov.wallet.payer)
    return await token.create_account(owner)


@fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@fixture(scope="module")
async def program(localnet) -> Program:
    """Create a Program instance."""
    workspace = create_workspace(PATH)
    return workspace["composite"]


@fixture(scope="module")
async def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    return program.provider


# @mark.asyncio
# async def test_main(provider: Provider):
#     watermelon_ido_amount = 5000000
#     usdc_mint_account = await create_mint(provider)
#     watermelon_mint_account = await create_mint(provider)
#     usdc_mint = usdc_mint_account.pubkey
#     watermelon_mint = watermelon_mint_account.pubkey
#     ido_authority_usdc = await create_token_account(
#         provider,
#         usdc_mint,
#         provider.wallet.public_key,
#     )
#     ido_authority_watermelon = await create_token_account(
#         provider,
#         watermelon_mint,
#         provider.wallet.public_key,
#     )
#     # Mint Watermelon tokens that will be distributed from the IDO pool.
#     await watermelon_mint_account.mint_to(
#         ido_authority_watermelon,
#         provider.wallet.public_key,
#         watermelon_ido_amount,
#     )
#     ido_authority_watermelon_account = await AsyncToken(
#         provider.client,
#         ido_authority_watermelon,
#         TOKEN_PROGRAM_ID,
#         provider.wallet.payer,
#     ).get_account_info(ido_authority_watermelon)
#     assert ido_authority_watermelon_account.amount == watermelon_ido_amount
