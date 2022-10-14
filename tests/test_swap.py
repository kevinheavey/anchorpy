from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple, AsyncGenerator
from contextlib import asynccontextmanager
from pyserum._layouts.instructions import INSTRUCTIONS_LAYOUT, InstructionType
from pytest import mark, fixture
from pytest_asyncio import fixture as async_fixture
from more_itertools import unique_everseen
from construct import Int64ul
from pyserum.instructions import InitializeMarketParams
from solana.keypair import Keypair
from solana.blockhash import Blockhash
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
from pyserum._layouts.open_orders import OPEN_ORDERS_LAYOUT
from anchorpy.program.context import Context
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.utils.token import create_mint_and_vault, get_token_account
from pyserum.enums import Side, OrderType
from anchorpy.provider import DEFAULT_OPTIONS, Provider, Wallet
from anchorpy import Program
from anchorpy.workspace import WorkspaceType

DEX_PID = PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin")
ONE_MILLION = 1_000_000
DECIMALS = 6
TAKER_FEE = 0.0022
PATH = Path("anchor/tests/swap/")
SLEEP_SECONDS = 15
workspace = workspace_fixture(
    "anchor/tests/swap/",
    build_cmd=(
        "cd deps/serum-dex/dex && cargo build-bpf && cd ../../../ && anchor build --skip-lint"
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
            provider.connection,
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
        except:  # noqa: E722,B001
            nonce += 1
    raise KeyError("Unable to find a viable program address nonce")


async def sign_transactions(
    transactions_and_signers: list[TransactionAndSigners],
    wallet: Wallet,
    client: AsyncClient,
) -> list[Transaction]:
    blockhash_resp = await client.get_latest_blockhash(Finalized)
    recent_blockhash = blockhash_resp.value.blockhash
    txs = []
    for transaction, signers in transactions_and_signers:
        transaction.recent_blockhash = Blockhash(str(recent_blockhash))
        all_signers = list(unique_everseen([wallet.payer] + signers))
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
            {
                "instruction_type": InstructionType.INITIALIZE_MARKET,
                "args": {
                    "base_lot_size": params.base_lot_size,
                    "quote_lot_size": params.quote_lot_size,
                    "fee_rate_bps": params.fee_rate_bps,
                    "vault_signer_nonce": params.vault_signer_nonce,
                    "quote_dust_threshold": params.quote_dust_threshold,
                },
            },
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
            lamports=base_vault_mbre_resp.value,
            space=base_vault_space,
            program_id=TOKEN_PROGRAM_ID,
        ),
    )
    create_quote_vault_instruction = create_account(
        CreateAccountParams(
            from_pubkey=wallet.public_key,
            new_account_pubkey=quote_vault.public_key,
            lamports=base_vault_mbre_resp.value,
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
            lamports=market_mbre_resp.value,
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
            lamports=request_queue_mbre_resp.value,
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
            lamports=event_queue_mbre_resp.value,
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
            lamports=bids_mbre_resp.value,
            space=bids_space,
            program_id=DEX_PID,
        ),
    )
    create_asks_instruction = create_account(
        CreateAccountParams(
            from_pubkey=wallet.public_key,
            new_account_pubkey=asks.public_key,
            lamports=bids_mbre_resp.value,
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
        client=provider.connection,
        wallet=provider.wallet,
        base_mint=base_mint,
        quote_mint=quote_mint,
        base_lot_size=100000,
        quote_lot_size=100,
        dex_program_id=DEX_PID,
        fee_rate_bps=0,
    )
    # await asyncio.sleep(SLEEP_SECONDS)
    market_a_usdc = await AsyncMarket.load(
        provider.connection, market_a_public_key, DEX_PID
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
            opts=provider.opts,
        )
        print(f"sent order {ask_idx}")
    print("finished sending asks")
    len_asks = len(asks)
    for bid_idx, bid in enumerate(bids):
        client_id = bid_idx + len_asks
        await market_a_usdc.place_order(
            payer=market_maker.quote_token,
            owner=market_maker.account,
            order_type=OrderType.POST_ONLY,
            side=Side.BUY,
            limit_price=bid[0],
            max_quantity=bid[1],
            client_id=client_id,
            opts=provider.opts,
        )
        print(f"sent order {client_id}")
    print("finished sending bids")
    return market_a_usdc


async def setup_two_markets(provider: Provider) -> OrderbookEnv:
    mint_a, god_a = await default_mint_and_vault(provider)
    mint_b, god_b = await default_mint_and_vault(provider)
    mint_usdc, god_usdc = await default_mint_and_vault(provider)
    amount = int(100000 * 10**DECIMALS)
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
def program(workspace: WorkspaceType) -> Program:
    return workspace["swap"]


@async_fixture(scope="module")
async def orderbook_env(program: Program) -> OrderbookEnv:
    return await setup_two_markets(program.provider)


@fixture(scope="module")
def market_a(orderbook_env: OrderbookEnv) -> AsyncMarket:
    return orderbook_env.market_a


@fixture(scope="module")
def market_b(orderbook_env: OrderbookEnv) -> AsyncMarket:
    return orderbook_env.market_b


@fixture(scope="module")
def market_a_vault_signer(market_a: AsyncMarket) -> PublicKey:
    return get_vault_owner_and_nonce(market_a.state.public_key())[0]


@fixture(scope="module")
def market_b_vault_signer(market_b: AsyncMarket) -> PublicKey:
    return get_vault_owner_and_nonce(market_b.state.public_key())[0]


@fixture(scope="module")
def open_orders_a() -> Keypair:
    return Keypair()


@fixture(scope="module")
def open_orders_b() -> Keypair:
    return Keypair()


@fixture(scope="module")
def swap_usdc_a_accounts(
    market_a: AsyncMarket,
    orderbook_env: OrderbookEnv,
    market_a_vault_signer: PublicKey,
    program: Program,
    open_orders_a: Keypair,
) -> dict[str, Any]:
    market_subdict = {
        "market": market_a.state.public_key(),
        "request_queue": market_a.state.request_queue(),
        "event_queue": market_a.state.event_queue(),
        "bids": market_a.state.bids(),
        "asks": market_a.state.asks(),
        "coin_vault": market_a.state.base_vault(),
        "pc_vault": market_a.state.quote_vault(),
        "vault_signer": market_a_vault_signer,
        "open_orders": open_orders_a.public_key,
        "order_payer_token_account": orderbook_env.god_usdc,
        "coin_wallet": orderbook_env.god_a,
    }
    return {
        "market": market_subdict,
        "pc_wallet": orderbook_env.god_usdc,
        "authority": program.provider.wallet.public_key,
        "dex_program": DEX_PID,
        "token_program": TOKEN_PROGRAM_ID,
        "rent": SYSVAR_RENT_PUBKEY,
    }


@fixture(scope="module")
def swap_a_usdc_accounts(
    orderbook_env: OrderbookEnv,
    swap_usdc_a_accounts: dict[str, Any],
) -> dict[str, Any]:
    market_subdict = {
        **swap_usdc_a_accounts["market"],
        "order_payer_token_account": orderbook_env.god_a,
    }
    return {**swap_usdc_a_accounts, "market": market_subdict}


@asynccontextmanager
async def balance_change(
    provider: Provider,
    addrs: list[PublicKey],
    deltas: list[
        float,
    ],
) -> AsyncGenerator:
    before_balances = []
    for addr in addrs:
        acc = await get_token_account(provider, addr)
        before_balances.append(acc.amount)
    yield
    after_balances = []
    for addr in addrs:
        acc = await get_token_account(provider, addr)
        after_balances.append(acc.amount)
    for before, after in zip(before_balances, after_balances):
        delta = (after - before) / ONE_MILLION
        deltas.append(delta)


@async_fixture(scope="module")
async def swap_usdc_to_a_and_init_open_orders(
    orderbook_env: OrderbookEnv,
    program: Program,
    swap_usdc_a_accounts: dict[str, Any],
    open_orders_a: Keypair,
    open_orders_b: Keypair,
) -> tuple[float, float, float, int]:
    expected_resultant_amount = 7.2
    best_offer_price = 6.041
    amount_to_spend = expected_resultant_amount * best_offer_price
    swap_amount = int((amount_to_spend / (1 - TAKER_FEE)) * ONE_MILLION)
    side = program.type["Side"]
    mbre_resp = (
        await program.provider.connection.get_minimum_balance_for_rent_exemption(
            OPEN_ORDERS_LAYOUT.sizeof()
        )
    )
    balance_needed = mbre_resp.value
    instructions = [
        make_create_account_instruction(
            owner_address=program.provider.wallet.public_key,
            new_account_address=open_orders_a.public_key,
            lamports=balance_needed,
            program_id=DEX_PID,
        ),
        make_create_account_instruction(
            owner_address=program.provider.wallet.public_key,
            new_account_address=open_orders_b.public_key,
            lamports=balance_needed,
            program_id=DEX_PID,
        ),
    ]
    addrs = [orderbook_env.god_a, orderbook_env.god_usdc]
    deltas: list[float] = []
    async with balance_change(program.provider, addrs, deltas):
        await program.rpc["swap"](
            side.Bid(),
            swap_amount,
            1,
            ctx=Context(
                accounts=swap_usdc_a_accounts,
                pre_instructions=instructions,
                signers=[open_orders_a, open_orders_b],
            ),
        )
    token_a_change, usdc_change = deltas
    return token_a_change, usdc_change, expected_resultant_amount, swap_amount


@mark.asyncio
async def test_swap_usdc_to_a(
    swap_usdc_to_a_and_init_open_orders: tuple[float, float, float, int]
) -> None:
    (
        token_a_change,
        usdc_change,
        expected_resultant_amount,
        swap_amount,
    ) = swap_usdc_to_a_and_init_open_orders
    assert token_a_change == expected_resultant_amount
    # TODO: check why this is slightly off
    # assert usdc_change == -swap_amount / ONE_MILLION


@mark.asyncio
async def test_swap_a_to_usdc(
    orderbook_env: OrderbookEnv,
    swap_usdc_to_a_and_init_open_orders: tuple[float, float, float, int],
    program: Program,
    swap_a_usdc_accounts: dict[str, Any],
) -> None:
    best_bid_price = 6.004
    swap_amount = 8.1
    amount_to_fill = swap_amount * best_bid_price
    expected_resultant_amount = int(  # noqa: F841
        amount_to_fill * (1 - TAKER_FEE) * ONE_MILLION,
    )
    side = program.type["Side"]
    addrs = [orderbook_env.god_a, orderbook_env.god_usdc]
    deltas: list[float] = []
    async with balance_change(program.provider, addrs, deltas):
        await program.rpc["swap"](
            side.Ask(),
            int(swap_amount * ONE_MILLION),
            int(swap_amount),
            ctx=Context(
                accounts=swap_a_usdc_accounts,
            ),
        )
    token_a_change, usdc_change = deltas
    assert token_a_change == -swap_amount
    # TODO: check why this is slightly off
    # assert usdc_change == expected_resultant_amount / ONE_MILLION


@mark.asyncio
async def test_swap_a_to_b(
    orderbook_env: OrderbookEnv,
    swap_usdc_to_a_and_init_open_orders: tuple[float, float, float, int],
    program: Program,
    market_a: AsyncMarket,
    market_b: AsyncMarket,
    market_a_vault_signer: PublicKey,
    market_b_vault_signer: PublicKey,
    open_orders_a: Keypair,
    open_orders_b: Keypair,
) -> None:
    swap_amount = 10
    from_subdict = {
        "market": market_a.state.public_key(),
        "request_queue": market_a.state.request_queue(),
        "event_queue": market_a.state.event_queue(),
        "bids": market_a.state.bids(),
        "asks": market_a.state.asks(),
        "coin_vault": market_a.state.base_vault(),
        "pc_vault": market_a.state.quote_vault(),
        "vault_signer": market_a_vault_signer,
        # User params.
        "open_orders": open_orders_a.public_key,
        # Swapping from A -> USDC.
        "order_payer_token_account": orderbook_env.god_a,
        "coin_wallet": orderbook_env.god_a,
    }
    to_subdict = {
        "market": market_b.state.public_key(),
        "request_queue": market_b.state.request_queue(),
        "event_queue": market_b.state.event_queue(),
        "bids": market_b.state.bids(),
        "asks": market_b.state.asks(),
        "coin_vault": market_b.state.base_vault(),
        "pc_vault": market_b.state.quote_vault(),
        "vault_signer": market_b_vault_signer,
        # User params.
        "open_orders": open_orders_b.public_key,
        # Swapping from USDC -> B.
        "order_payer_token_account": orderbook_env.god_usdc,
        "coin_wallet": orderbook_env.god_b,
    }
    accounts = {
        "from": from_subdict,
        "to": to_subdict,
        "pc_wallet": orderbook_env.god_usdc,
        "authority": program.provider.wallet.public_key,
        "dex_program": DEX_PID,
        "token_program": TOKEN_PROGRAM_ID,
        "rent": SYSVAR_RENT_PUBKEY,
    }
    addrs = [orderbook_env.god_a, orderbook_env.god_b, orderbook_env.god_usdc]
    deltas: list[float] = []
    async with balance_change(program.provider, addrs, deltas):
        await program.rpc["swap_transitive"](
            int(swap_amount * ONE_MILLION),
            int(swap_amount - 1),
            ctx=Context(
                accounts=accounts,
            ),
        )
    token_a_change, token_b_change, usdc_change = deltas
    assert token_a_change == -swap_amount
    # TODO: check why this is slightly off
    # assert token_b_change == 9.8  # noqa: WPS459
    # assert usdc_change == 0


@mark.asyncio
async def test_swap_b_to_a(
    orderbook_env: OrderbookEnv,
    swap_usdc_to_a_and_init_open_orders: tuple[float, float, float, int],
    program: Program,
    market_a: AsyncMarket,
    market_b: AsyncMarket,
    market_a_vault_signer: PublicKey,
    market_b_vault_signer: PublicKey,
    open_orders_a: Keypair,
    open_orders_b: Keypair,
) -> None:
    swap_amount = 23
    from_subdict = {
        "market": market_b.state.public_key(),
        "request_queue": market_b.state.request_queue(),
        "event_queue": market_b.state.event_queue(),
        "bids": market_b.state.bids(),
        "asks": market_b.state.asks(),
        "coin_vault": market_b.state.base_vault(),
        "pc_vault": market_b.state.quote_vault(),
        "vault_signer": market_b_vault_signer,
        # User params.
        "open_orders": open_orders_b.public_key,
        # Swapping from B -> USDC.
        "order_payer_token_account": orderbook_env.god_b,
        "coin_wallet": orderbook_env.god_b,
    }
    to_subdict = {
        "market": market_a.state.public_key(),
        "request_queue": market_a.state.request_queue(),
        "event_queue": market_a.state.event_queue(),
        "bids": market_a.state.bids(),
        "asks": market_a.state.asks(),
        "coin_vault": market_a.state.base_vault(),
        "pc_vault": market_a.state.quote_vault(),
        "vault_signer": market_a_vault_signer,
        # User params.
        "open_orders": open_orders_a.public_key,
        # Swapping from USDC -> B.
        "order_payer_token_account": orderbook_env.god_usdc,
        "coin_wallet": orderbook_env.god_a,
    }
    accounts = {
        "from": from_subdict,
        "to": to_subdict,
        "pc_wallet": orderbook_env.god_usdc,
        "authority": program.provider.wallet.public_key,
        "dex_program": DEX_PID,
        "token_program": TOKEN_PROGRAM_ID,
        "rent": SYSVAR_RENT_PUBKEY,
    }
    addrs = [orderbook_env.god_a, orderbook_env.god_b, orderbook_env.god_usdc]
    deltas: list[float] = []
    async with balance_change(program.provider, addrs, deltas):
        await program.rpc["swap_transitive"](
            int(swap_amount * ONE_MILLION),
            int(swap_amount - 1),
            ctx=Context(
                accounts=accounts,
            ),
        )
    token_a_change, token_b_change, usdc_change = deltas
    # TODO: check why this is slightly off
    # assert token_a_change == 22.6  # noqa: WPS459
    assert token_b_change == -swap_amount
    # assert usdc_change == 0
