"""Mimics anchor/tests/multisig."""
from pathlib import Path
from typing import AsyncGenerator, List, Tuple
from dataclasses import replace

from pytest import mark, fixture
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.transaction import AccountMeta

from anchorpy import Program, create_workspace, close_workspace, Context, Provider
from anchorpy.pytest_plugin import localnet_fixture

PATH = Path("anchor/tests/multisig/")

CreatedMultisig = Tuple[Keypair, int, List[PublicKey], int, PublicKey, Keypair, Keypair]
CreatedTransaction = Tuple[
    Keypair, List[dict], bytes, Keypair, PublicKey, List[PublicKey]
]

localnet = localnet_fixture(PATH)


@fixture(scope="module")
async def program(localnet) -> AsyncGenerator[Program, None]:
    """Create a Program instance."""
    workspace = create_workspace(PATH)
    yield workspace["multisig"]
    await close_workspace(workspace)


@fixture(scope="module")
async def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    return program.provider


@fixture(scope="module")
async def created_multisig(program: Program) -> CreatedMultisig:
    """Run the create_multisig RPC function."""
    multisig = Keypair()
    multisig_signer, nonce = PublicKey.find_program_address(
        [bytes(multisig.public_key)], program.program_id
    )
    multisig_size = 200
    owner_a, owner_b, owner_c = Keypair(), Keypair(), Keypair()
    owners = [owner_a.public_key, owner_b.public_key, owner_c.public_key]
    threshold = 2
    await program.rpc["create_multisig"](
        owners,
        threshold,
        nonce,
        ctx=Context(
            accounts={
                "multisig": multisig.public_key,
                "rent": SYSVAR_RENT_PUBKEY,
            },
            instructions=[
                await program.account["Multisig"].create_instruction(
                    multisig, multisig_size
                ),
            ],
            signers=[multisig],
        ),
    )
    return multisig, nonce, owners, threshold, multisig_signer, owner_a, owner_b


@mark.asyncio
async def test_created_multisig(
    created_multisig: CreatedMultisig,
    program: Program,
) -> None:
    multisig, nonce, owners, threshold = created_multisig[:4]
    multisig_account = await program.account["Multisig"].fetch(multisig.public_key)
    assert multisig_account.nonce == nonce
    assert multisig_account.threshold == threshold
    assert multisig_account.owners == owners


@fixture(scope="module")
async def created_transaction(
    program: Program,
    created_multisig: CreatedMultisig,
) -> CreatedTransaction:
    owner_d = Keypair()
    multisig, _, owners, _, multisig_signer, owner_a, _ = created_multisig
    accounts = [
        program.type["TransactionAccount"](
            pubkey=multisig.public_key,
            is_writable=True,
            is_signer=False,
        ),
        program.type["TransactionAccount"](
            pubkey=multisig_signer,
            is_writable=False,
            is_signer=True,
        ),
    ]
    new_owners = [*owners[:2], owner_d.public_key]
    data = program.coder.instruction.encode("set_owners", {"owners": new_owners})
    transaction = Keypair()
    tx_size = 1000
    await program.rpc["create_transaction"](
        program.program_id,
        accounts,
        data,
        ctx=Context(
            accounts={
                "multisig": multisig.public_key,
                "transaction": transaction.public_key,
                "proposer": owner_a.public_key,
                "rent": SYSVAR_RENT_PUBKEY,
            },
            instructions=[
                await program.account["Transaction"].create_instruction(
                    transaction,
                    tx_size,
                ),
            ],
            signers=[transaction, owner_a],
        ),
    )
    return transaction, accounts, data, multisig, multisig_signer, new_owners


@mark.asyncio
async def test_created_transaction(
    created_transaction: CreatedTransaction,
    program: Program,
) -> None:
    transaction, accounts, data, multisig, _, _ = created_transaction
    tx_account = await program.account["Transaction"].fetch(transaction.public_key)
    assert tx_account.program_id == program.program_id
    assert tx_account.accounts == accounts
    assert tx_account.data == data
    assert tx_account.multisig == multisig.public_key
    assert tx_account.did_execute is False


@fixture(scope="module")
async def executed_transaction(
    program: Program,
    created_transaction: CreatedTransaction,
    created_multisig: CreatedMultisig,
) -> None:
    transaction, _, _, multisig, multisig_signer, _ = created_transaction
    owner_b = created_multisig[6]
    await program.rpc["approve"](
        ctx=Context(
            accounts={
                "multisig": multisig.public_key,
                "transaction": transaction.public_key,
                "owner": owner_b.public_key,
            },
            signers=[owner_b],
        ),
    )
    remaining_accounts_raw = program.instruction["set_owners"].accounts(
        {"multisig": multisig.public_key, "multisig_signer": multisig_signer}
    )
    with_corrected_signer = []
    for meta in remaining_accounts_raw:
        if meta.pubkey == multisig_signer:
            to_append = replace(meta, is_signer=False)
        else:
            to_append = meta
        with_corrected_signer.append(to_append)
    remaining_accounts = with_corrected_signer + [
        AccountMeta(pubkey=program.program_id, is_signer=False, is_writable=False)
    ]
    ctx = Context(
        accounts={
            "multisig": multisig.public_key,
            "multisig_signer": multisig_signer,
            "transaction": transaction.public_key,
        },
        remaining_accounts=remaining_accounts,
    )
    await program.rpc["execute_transaction"](ctx=ctx)


@mark.asyncio
async def test_executed_transaction(
    created_multisig: CreatedMultisig,
    created_transaction: CreatedTransaction,
    executed_transaction: None,
    program: Program,
) -> None:
    multisig, nonce, _, threshold = created_multisig[:4]
    new_owners = created_transaction[5]
    multisig_account = await program.account["Multisig"].fetch(multisig.public_key)
    assert multisig_account.nonce == nonce
    assert multisig_account.threshold == threshold
    assert multisig_account.owners == new_owners
