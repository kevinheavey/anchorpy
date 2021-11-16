"""Mimics anchor/tests/escrow/tests/escrow.js."""
from pathlib import Path
from typing import AsyncGenerator

from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.commitment import Confirmed
from solana.system_program import SYS_PROGRAM_ID
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID

from pytest import fixture, mark
from anchorpy import Program, Provider, create_workspace, close_workspace
from anchorpy.program.context import Context
from anchorpy.pytest_plugin import get_localnet

PATH = Path("anchor/tests/escrow")
INITIALIZER_AMOUNT = 500
TAKER_AMOUNT = 1000

localnet = get_localnet(PATH)

InitializeEscrowStateResult = tuple[
    AsyncToken, AsyncToken, PublicKey, PublicKey, PublicKey, PublicKey, Keypair
]
InitializeEscrowResult = tuple[Keypair, PublicKey]


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
async def initialize_escrow_state(
    program: Program, provider: Provider
) -> InitializeEscrowStateResult:
    payer = Keypair()
    mint_authority = Keypair()
    airdrop_resp = await provider.client.request_airdrop(payer.public_key, 10000000000)
    await provider.client.confirm_transaction(airdrop_resp["result"], Confirmed)
    mint_airdrop_resp = await provider.client.request_airdrop(
        mint_authority.public_key, 10000000000
    )
    await provider.client.confirm_transaction(mint_airdrop_resp["result"], Confirmed)
    mint_a = await AsyncToken.create_mint(
        provider.client,
        payer,
        mint_authority.public_key,
        0,
        TOKEN_PROGRAM_ID,
    )
    mint_b = await AsyncToken.create_mint(
        provider.client,
        payer,
        mint_authority.public_key,
        0,
        TOKEN_PROGRAM_ID,
    )
    initializer_token_account_a = await mint_a.create_account(
        provider.wallet.public_key,
    )
    taker_token_account_a = await mint_a.create_account(provider.wallet.public_key)
    initializer_token_account_b = await mint_b.create_account(
        provider.wallet.public_key,
    )
    taker_token_account_b = await mint_b.create_account(provider.wallet.public_key)
    mint_to_a_resp = await mint_a.mint_to(
        initializer_token_account_a,
        mint_authority.public_key,
        INITIALIZER_AMOUNT,
        [mint_authority],
    )
    await provider.client.confirm_transaction(mint_to_a_resp["result"], Confirmed)

    mint_to_b_resp = await mint_b.mint_to(
        taker_token_account_b,
        mint_authority.public_key,
        TAKER_AMOUNT,
        [mint_authority],
    )
    await provider.client.confirm_transaction(mint_to_b_resp["result"], Confirmed)
    return (
        mint_a,
        mint_b,
        initializer_token_account_a,
        initializer_token_account_b,
        taker_token_account_a,
        taker_token_account_b,
        mint_authority,
    )


@mark.asyncio
async def test_initialized_escrow_state(
    initialize_escrow_state: InitializeEscrowStateResult,
) -> None:
    (
        mint_a,
        mint_b,
        initializer_token_account_a,
        initializer_token_account_b,
        taker_token_account_a,
        taker_token_account_b,
        mint_authority,
    ) = initialize_escrow_state
    _initializer_token_account_a = await mint_a.get_account_info(
        initializer_token_account_a,
    )
    _taker_token_account_b = await mint_b.get_account_info(taker_token_account_b)
    assert _initializer_token_account_a.amount == INITIALIZER_AMOUNT
    assert _taker_token_account_b.amount == TAKER_AMOUNT


@fixture(scope="module")
async def initialize_escrow(
    program: Program,
    provider: Provider,
    initialize_escrow_state: InitializeEscrowStateResult,
) -> InitializeEscrowResult:
    (
        mint_a,
        mint_b,
        initializer_token_account_a,
        initializer_token_account_b,
        taker_token_account_a,
        taker_token_account_b,
        mint_authority,
    ) = initialize_escrow_state
    escrow_account = Keypair()
    ctx = Context(
        accounts={
            "initializer": provider.wallet.public_key,
            "initializerDepositTokenAccount": initializer_token_account_a,
            "initializerReceiveTokenAccount": initializer_token_account_b,
            "escrowAccount": escrow_account.public_key,
            "systemProgram": SYS_PROGRAM_ID,
            "tokenProgram": TOKEN_PROGRAM_ID,
        },
        signers=[escrow_account],
    )
    await program.rpc["initializeEscrow"](INITIALIZER_AMOUNT, TAKER_AMOUNT, ctx=ctx)
    pda, _ = PublicKey.find_program_address([b"escrow"], program.program_id)
    return escrow_account, pda


@mark.asyncio
async def test_initialize_escrow(
    initialize_escrow: InitializeEscrowResult,
    program: Program,
    provider: Provider,
    initialize_escrow_state: InitializeEscrowStateResult,
) -> None:
    (
        mint_a,
        mint_b,
        initializer_token_account_a,
        initializer_token_account_b,
        taker_token_account_a,
        taker_token_account_b,
        mint_authority,
    ) = initialize_escrow_state
    escrow_account, pda = initialize_escrow
    _initializer_token_account_a = await mint_a.get_account_info(
        initializer_token_account_a
    )
    _escrow_account = await program.account["EscrowAccount"].fetch(
        escrow_account.public_key
    )
    assert _initializer_token_account_a.owner == pda

    # Check that the values in the escrow account match what we expect.
    assert _escrow_account.initializerKey == provider.wallet.public_key
    assert _escrow_account.initializerAmount == INITIALIZER_AMOUNT
    assert _escrow_account.takerAmount == TAKER_AMOUNT
    assert _escrow_account.initializerDepositTokenAccount == initializer_token_account_a
    assert _escrow_account.initializerReceiveTokenAccount == initializer_token_account_b


@mark.asyncio
async def test_exchange_escrow(
    initialize_escrow: InitializeEscrowResult,
    program: Program,
    provider: Provider,
    initialize_escrow_state: InitializeEscrowStateResult,
) -> None:
    (
        mint_a,
        mint_b,
        initializer_token_account_a,
        initializer_token_account_b,
        taker_token_account_a,
        taker_token_account_b,
        mint_authority,
    ) = initialize_escrow_state
    escrow_account, pda = initialize_escrow
    await program.rpc["exchange"](
        ctx=Context(
            accounts={
                "taker": provider.wallet.public_key,
                "takerDepositTokenAccount": taker_token_account_b,
                "takerReceiveTokenAccount": taker_token_account_a,
                "pdaDepositTokenAccount": initializer_token_account_a,
                "initializerReceiveTokenAccount": initializer_token_account_b,
                "initializerMainAccount": provider.wallet.public_key,
                "escrowAccount": escrow_account.public_key,
                "pdaAccount": pda,
                "tokenProgram": TOKEN_PROGRAM_ID,
            },
        )
    )
    _taker_token_account_a = await mint_a.get_account_info(taker_token_account_a)
    _taker_token_account_b = await mint_b.get_account_info(taker_token_account_b)
    _initializer_token_account_a = await mint_a.get_account_info(
        initializer_token_account_a
    )
    _initializer_token_account_b = await mint_b.get_account_info(
        initializer_token_account_b
    )
    # Check that the initializer gets back ownership of their token account.
    assert _taker_token_account_a.owner == provider.wallet.public_key

    assert _taker_token_account_a.amount == INITIALIZER_AMOUNT
    assert _initializer_token_account_a.amount == 0
    assert _initializer_token_account_b.amount == TAKER_AMOUNT
    assert _taker_token_account_b.amount == 0


@mark.asyncio
async def test_init_and_cancel_escrow(
    initialize_escrow: InitializeEscrowResult,
    program: Program,
    provider: Provider,
    initialize_escrow_state: InitializeEscrowStateResult,
) -> None:
    (
        mint_a,
        mint_b,
        initializer_token_account_a,
        initializer_token_account_b,
        taker_token_account_a,
        taker_token_account_b,
        mint_authority,
    ) = initialize_escrow_state
    escrow_account, pda = initialize_escrow
    # Put back tokens into initializer token A account.
    mint_to_resp = await mint_a.mint_to(
        dest=initializer_token_account_a,
        mint_authority=mint_authority.public_key,
        multi_signers=[mint_authority],
        amount=INITIALIZER_AMOUNT,
    )
    await provider.client.confirm_transaction(mint_to_resp["result"], Confirmed)
    new_escrow = Keypair()
    await program.rpc["initializeEscrow"](
        INITIALIZER_AMOUNT,
        TAKER_AMOUNT,
        ctx=Context(
            accounts={
                "initializer": provider.wallet.public_key,
                "initializerDepositTokenAccount": initializer_token_account_a,
                "initializerReceiveTokenAccount": initializer_token_account_b,
                "escrowAccount": new_escrow.public_key,
                "systemProgram": SYS_PROGRAM_ID,
                "tokenProgram": TOKEN_PROGRAM_ID,
            },
            signers=[new_escrow],
        ),
    )

    _initializer_token_account_a = await mint_a.get_account_info(
        initializer_token_account_a
    )

    # Check that the new owner is the PDA.
    assert _initializer_token_account_a.owner == pda

    # Cancel the escrow.
    await program.rpc["cancelEscrow"](
        ctx=Context(
            accounts={
                "initializer": provider.wallet.public_key,
                "pdaDepositTokenAccount": initializer_token_account_a,
                "pdaAccount": pda,
                "escrowAccount": new_escrow.public_key,
                "tokenProgram": TOKEN_PROGRAM_ID,
            },
        )
    )

    # Check the final owner should be the provider public key.
    _initializer_token_account_a = await mint_a.get_account_info(
        initializer_token_account_a
    )
    assert _initializer_token_account_a.owner == provider.wallet.public_key

    # Check all the funds are still there.
    assert _initializer_token_account_a.amount == INITIALIZER_AMOUNT
