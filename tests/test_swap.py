from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, AsyncGenerator
import asyncio
from pyserum._layouts.instructions import INSTRUCTIONS_LAYOUT, InstructionType
from pytest import mark, fixture
from construct import Int64ul
from pyserum.instructions import InitializeMarketParams
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import AccountMeta, Transaction, TransactionInstruction
from solana.rpc.async_api import AsyncClient
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.rpc.commitment import Finalized
from solana.system_program import (
    CreateAccountParams,
    create_account,
    transfer,
    TransferParams,
)
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.async_client import AsyncToken
from spl.token.instructions import (
    transfer_checked,
    TransferCheckedParams,
    initialize_account,
    InitializeAccountParams,
)
from pyserum.open_orders_account import make_create_account_instruction
from pyserum.market import AsyncMarket
from pyserum._layouts.market import MARKET_LAYOUT
from anchorpy.utils.token import create_mint_and_vault
from pyserum.enums import Side, OrderType
from anchorpy.provider import DEFAULT_OPTIONS, Provider, Wallet
from anchorpy import create_workspace, get_localnet, close_workspace, Program

DEX_PID = PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin")

DECIMALS = 6
TAKER_FEE = 0.0022
PATH = Path("anchor/tests/swap/")
localnet = get_localnet(
    PATH,
    build_cmd=(
        "cd deps/serum-dex/dex && cargo build-bpf && cd ../../../ && anchor build"
    ),
)


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


class TransactionAndSigners(NamedTuple):
    transaction: Transaction
    signers: list[Keypair]


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
    for god, mint, amount in mints:
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
        transfer_checked_params = TransferCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            source=god,
            mint=mint,
            dest=market_maker_token_a,
            owner=provider.wallet.public_key,
            amount=amount,
            decimals=DECIMALS,
        )
        transfer_checked_instruction = transfer_checked(transfer_checked_params)
        create_transfer_tx.add(transfer_checked_instruction)
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


async def sign_transactions(
    transactions_and_signers: list[TransactionAndSigners],
    wallet: Wallet,
    client: AsyncClient,
) -> list[Transaction]:
    blockhash_resp = await client.get_recent_blockhash(Finalized)
    recent_blockhash = blockhash_resp["result"]["value"]["blockhash"]
    txs = []
    for transaction, signers in transactions_and_signers:
        transaction.recent_blockhash = recent_blockhash
        all_signers = [wallet.payer] + signers
        transaction.sign(*all_signers)
        txs.append(transaction)
    return txs


# differs from pyserum
def initialize_market(params: InitializeMarketParams) -> TransactionInstruction:
    """Generate a transaction instruction to initialize a Serum market."""
    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=params.market, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.request_queue, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.event_queue, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.bids, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.asks, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.base_vault, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.quote_vault, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.base_mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=params.quote_mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
        ],
        program_id=params.program_id,
        data=INSTRUCTIONS_LAYOUT.build(
            dict(
                instruction_type=InstructionType.INITIALIZE_MARKET,
                args=dict(
                    base_lot_size=params.base_lot_size,
                    quote_lot_size=params.quote_lot_size,
                    fee_rate_bps=params.fee_rate_bps,
                    vault_signer_nonce=params.vault_signer_nonce,
                    quote_dust_threshold=params.quote_dust_threshold,
                ),
            ),
        ),
    )


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
    tx1 = Transaction()
    base_vault_space = 165
    base_vault_mbre_resp = await client.get_minimum_balance_for_rent_exemption(
        base_vault_space,
    )
    create_base_vault_instruction = create_account(
        CreateAccountParams(
            from_pubkey=wallet.public_key,
            new_account_pubkey=base_vault.public_key,
            lamports=base_vault_mbre_resp["result"],
            space=base_vault_space,
            program_id=TOKEN_PROGRAM_ID,
        ),
    )
    create_quote_vault_instruction = create_account(
        CreateAccountParams(
            from_pubkey=wallet.public_key,
            new_account_pubkey=quote_vault.public_key,
            lamports=base_vault_mbre_resp["result"],
            space=base_vault_space,
            program_id=TOKEN_PROGRAM_ID,
        ),
    )
    initialize_base_vault_instruction = initialize_account(
        InitializeAccountParams(
            program_id=TOKEN_PROGRAM_ID,
            account=base_vault.public_key,
            mint=base_mint,
            owner=vault_owner,
        ),
    )
    initialize_quote_vault_instruction = initialize_account(
        InitializeAccountParams(
            program_id=TOKEN_PROGRAM_ID,
            account=quote_vault.public_key,
            mint=quote_mint,
            owner=vault_owner,
        ),
    )
    tx1.add(
        create_base_vault_instruction,
        create_quote_vault_instruction,
        initialize_base_vault_instruction,
        initialize_quote_vault_instruction,
    )
    tx2 = Transaction()
    market_space = MARKET_LAYOUT.sizeof()
    market_mbre_resp = await client.get_minimum_balance_for_rent_exemption(market_space)
    create_market_instruction = create_account(
        CreateAccountParams(
            from_pubkey=wallet.public_key,
            new_account_pubkey=market.public_key,
            lamports=market_mbre_resp["result"],
            space=market_space,
            program_id=DEX_PID,
        ),
    )
    request_queue_space = 5120 + 12
    request_queue_mbre_resp = await client.get_minimum_balance_for_rent_exemption(
        request_queue_space,
    )
    create_request_queue_instruction = create_account(
        CreateAccountParams(
            from_pubkey=wallet.public_key,
            new_account_pubkey=request_queue.public_key,
            lamports=request_queue_mbre_resp["result"],
            space=request_queue_space,
            program_id=DEX_PID,
        ),
    )
    event_queue_space = 262144 + 12
    event_queue_mbre_resp = await client.get_minimum_balance_for_rent_exemption(
        event_queue_space,
    )
    create_event_queue_instruction = create_account(
        CreateAccountParams(
            from_pubkey=wallet.public_key,
            new_account_pubkey=event_queue.public_key,
            lamports=event_queue_mbre_resp["result"],
            space=event_queue_space,
            program_id=DEX_PID,
        ),
    )
    bids_space = 65536 + 12
    bids_mbre_resp = await client.get_minimum_balance_for_rent_exemption(
        bids_space,
    )
    create_bids_instruction = create_account(
        CreateAccountParams(
            from_pubkey=wallet.public_key,
            new_account_pubkey=bids.public_key,
            lamports=bids_mbre_resp["result"],
            space=bids_space,
            program_id=DEX_PID,
        ),
    )
    create_asks_instruction = create_account(
        CreateAccountParams(
            from_pubkey=wallet.public_key,
            new_account_pubkey=asks.public_key,
            lamports=bids_mbre_resp["result"],
            space=bids_space,
            program_id=DEX_PID,
        ),
    )
    init_market_instructions = initialize_market(
        InitializeMarketParams(
            market=market.public_key,
            request_queue=request_queue.public_key,
            event_queue=event_queue.public_key,
            bids=bids.public_key,
            asks=asks.public_key,
            base_vault=base_vault.public_key,
            quote_vault=quote_vault.public_key,
            base_mint=base_mint,
            quote_mint=quote_mint,
            base_lot_size=base_lot_size,
            quote_lot_size=quote_lot_size,
            fee_rate_bps=fee_rate_bps,
            vault_signer_nonce=vault_signer_nonce,
            quote_dust_threshold=quote_dust_threshold,
            program_id=DEX_PID,
        ),
    )
    tx2.add(
        create_market_instruction,
        create_request_queue_instruction,
        create_event_queue_instruction,
        create_bids_instruction,
        create_asks_instruction,
        init_market_instructions,
    )
    transactions_and_signers = [
        TransactionAndSigners(tx1, [base_vault, quote_vault]),
        TransactionAndSigners(tx2, [market, request_queue, event_queue, bids, asks]),
    ]
    signed_transactions = await sign_transactions(
        transactions_and_signers, wallet, client
    )
    for signed_transaction in signed_transactions:
        await client.send_raw_transaction(
            signed_transaction.serialize(), opts=DEFAULT_OPTIONS
        )
    return market.public_key


async def setup_market(
    provider: Provider,
    market_maker: MarketMakerSetupMarket,
    base_mint: PublicKey,
    quote_mint: PublicKey,
    bids: list[tuple[float, float]],
    asks: list[tuple[float, float]],
) -> AsyncMarket:
    market_a_public_key = await list_market(
        client=provider.client,
        wallet=provider.wallet,
        base_mint=base_mint,
        quote_mint=quote_mint,
        base_lot_size=100000,
        quote_lot_size=100,
        dex_program_id=DEX_PID,
        fee_rate_bps=0,
    )
    market_a_usdc = await AsyncMarket.load(
        provider.client, market_a_public_key, DEX_PID
    )
    for ask_idx, ask in enumerate(asks):
        await market_a_usdc.place_order(
            payer=market_maker.base_token,
            owner=market_maker.account,
            order_type=OrderType.POST_ONLY,
            side=Side.SELL,
            limit_price=ask[0],
            max_quantity=ask[1],
            client_id=ask_idx,
        )
    len_asks = len(asks)
    for bid_idx, bid in enumerate(bids):
        await market_a_usdc.place_order(
            payer=market_maker.base_token,
            owner=market_maker.account,
            order_type=OrderType.POST_ONLY,
            side=Side.BUY,
            limit_price=bid[0],
            max_quantity=bid[1],
            client_id=bid_idx + len_asks,
        )
    return market_a_usdc


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
        mints,
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
    market_a_usdc = await setup_market(
        provider=provider,
        base_mint=mint_a,
        quote_mint=mint_usdc,
        market_maker=MarketMakerSetupMarket(
            account=market_maker.account,
            base_token=market_maker.tokens[str(mint_a)],
            quote_token=market_maker.tokens[str(mint_usdc)],
        ),
        bids=bids,
        asks=asks,
    )
    market_b_usdc = await setup_market(
        provider=provider,
        base_mint=mint_b,
        quote_mint=mint_usdc,
        market_maker=MarketMakerSetupMarket(
            account=market_maker.account,
            base_token=market_maker.tokens[str(mint_b)],
            quote_token=market_maker.tokens[str(mint_usdc)],
        ),
        bids=bids,
        asks=asks,
    )
    return OrderbookEnv(
        market_a=market_a_usdc,
        market_b=market_b_usdc,
        market_maker=market_maker,
        mint_a=mint_a,
        mint_b=mint_b,
        usdc=mint_usdc,
        god_a=god_a,
        god_b=god_b,
        god_usdc=god_usdc,
    )


@fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@fixture(scope="module")
async def workspace(localnet) -> AsyncGenerator[dict[str, Program], None]:
    wspace = create_workspace(PATH)
    yield wspace
    await close_workspace(wspace)


@fixture(scope="module")
async def program(workspace: dict[str, Program]) -> Program:
    return workspace["swap"]


@fixture(scope="module")
async def orderbook_env(program: Program) -> OrderbookEnv:
    return await setup_two_markets(program.provider)


@mark.asyncio
async def test_main(orderbook_env: OrderbookEnv) -> None:
    print(orderbook_env)
