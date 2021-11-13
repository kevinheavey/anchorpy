from dataclasses import dataclass
from typing import NamedTuple
from construct import Int64ul
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction
from solana.rpc.async_api import AsyncClient
from solana.system_program import transfer, TransferParams
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.async_client import AsyncToken
from spl.token.instructions import (
    transfer as token_transfer,
    TransferParams as TokenTransferParams,
)
from pyserum.open_orders_account import make_create_account_instruction
from pyserum.market import AsyncMarket
from anchorpy.utils.token import create_mint_and_vault
from anchorpy.provider import Provider, Wallet

DEX_PID = PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin")

DECIMALS = 6


@dataclass
class MarketMaker:
    tokens: dict[str, PublicKey]
    account: Keypair


@dataclass
class MarketMakerSetupMarket:
    account: Keypair
    base_token: PublicKey
    quote_token: PublicKey


class MintRecord(NamedTuple):
    god: PublicKey
    mint: PublicKey
    amount: int


@dataclass
class OrderbookEnv:
    market_a: AsyncMarket
    market_b: AsyncMarket
    market_maker: MarketMaker
    mint_a: PublicKey
    mint_b: PublicKey
    usdc: PublicKey
    god_a: PublicKey
    god_b: PublicKey
    god_usdc: PublicKey


async def fund_account(provider: Provider, mints: list[MintRecord]) -> MarketMaker:
    market_maker_account = Keypair()
    market_maker = MarketMaker(tokens={}, account=market_maker_account)
    # Transfer lamports to market maker.
    transfer_tx = Transaction()
    transfer_tx.add(
        transfer(
            TransferParams(
                from_pubkey=provider.wallet.public_key,
                to_pubkey=market_maker_account.public_key,
                lamports=100000000000,
            ),
        ),
    )
    await provider.send(transfer_tx)
    # Transfer SPL tokens to the market maker.
    for mint, god, amount in mints:
        mint_a_client = AsyncToken(
            provider.client,
            mint,
            TOKEN_PROGRAM_ID,
            provider.wallet.payer,
        )
        market_maker_token_a = await mint_a_client.create_account(
            market_maker_account.public_key,
        )
        create_transfer_tx = Transaction()
        create_transfer_tx.add(
            token_transfer(
                TokenTransferParams(
                    program_id=TOKEN_PROGRAM_ID,
                    source=god,
                    dest=market_maker_token_a,
                    owner=provider.wallet.public_key,
                    amount=amount,
                ),
            ),
        )
        await provider.send(create_transfer_tx)
        market_maker.tokens[str(mint)] = market_maker_token_a
    return market_maker


async def default_mint_and_vault(provider: Provider) -> tuple[PublicKey, PublicKey]:
    return await create_mint_and_vault(provider, 1000000000000000, None, DECIMALS)


def get_vault_owner_and_nonce(
    market_pubkey: PublicKey,
    dex_program_id: PublicKey = DEX_PID,
) -> tuple[PublicKey, int]:
    nonce = 0
    while nonce < 255:
        try:
            vault_owner = PublicKey.create_program_address(
                [bytes(market_pubkey), Int64ul.build(nonce)],
                program_id=dex_program_id,
            )
            return vault_owner, nonce
        except:
            nonce += 1
    raise KeyError("Unable to find a viable program address nonce")


async def list_market(
    client: AsyncClient,
    wallet: Wallet,
    base_mint: PublicKey,
    quote_mint: PublicKey,
    base_lot_size: int,
    quote_lot_size: int,
    dex_program_id: PublicKey,
    fee_rate_bps: int,
) -> PublicKey:
    market = Keypair()
    request_queue = Keypair()
    event_queue = Keypair()
    bids = Keypair()
    asks = Keypair()
    base_vault = Keypair()
    quote_vault = Keypair()
    quote_dust_threshold = 100
    vault_owner, vault_signer_nonce = get_vault_owner_and_nonce(
        market.public_key,
        dex_program_id,
    )


async def setup_market(
    provider: Provider,
    market_maker: MarketMakerSetupMarket,
    base_mint: PublicKey,
    quote_mint: PublicKey,
    bids: list[tuple[int, int]],
    asks: list[tuple[int, int]],
) -> AsyncMarket:
    pass


async def setup_two_markets(provider: Provider) -> OrderbookEnv:
    mint_a, god_a = await default_mint_and_vault(provider)
    mint_b, god_b = await default_mint_and_vault(provider)
    mint_usdc, god_usdc = await default_mint_and_vault(provider)
    amount = int(100000 * 10 ** DECIMALS)
    mints = [
        MintRecord(god_a, mint_a, amount),
        MintRecord(god_b, mint_b, amount),
        MintRecord(god_usdc, mint_usdc, amount),
    ]
    market_maker = await fund_account(
        provider,
    )
    asks = [
        (6.041, 7.8),
        (6.051, 72.3),
        (6.055, 5.4),
        (6.067, 15.7),
        (6.077, 390.0),
        (6.09, 24.0),
        (6.11, 36.3),
        (6.133, 300.0),
        (6.167, 687.8),
    ]
    bids = [
        (6.004, 8.5),
        (5.995, 12.9),
        (5.987, 6.2),
        (5.978, 15.3),
        (5.965, 82.8),
        (5.961, 25.4),
    ]
