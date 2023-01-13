"""Mimics anchor/tests/multisig."""
from anchorpy import Context, Program, Provider
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType
from pytest import fixture, mark
from pytest_asyncio import fixture as async_fixture
from solders.instruction import AccountMeta
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.sysvar import RENT

CreatedMultisig = tuple[Keypair, int, list[Pubkey], int, Pubkey, Keypair, Keypair]
CreatedTransaction = tuple[Keypair, list[dict], bytes, Keypair, Pubkey, list[Pubkey]]

workspace = workspace_fixture(
    "anchor/tests/multisig/", build_cmd="anchor build --skip-lint"
)


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    """Create a Program instance."""
    return workspace["multisig"]


@fixture(scope="module")
def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    return program.provider


@async_fixture(scope="module")
async def created_multisig(program: Program) -> CreatedMultisig:
    """Run the create_multisig RPC function."""
    multisig = Keypair()
    multisig_signer, nonce = Pubkey.find_program_address(
        [bytes(multisig.pubkey())], program.program_id
    )
    multisig_size = 200
    owner_a, owner_b, owner_c = Keypair(), Keypair(), Keypair()
    owners = [owner_a.pubkey(), owner_b.pubkey(), owner_c.pubkey()]
    threshold = 2
    await program.rpc["create_multisig"](
        owners,
        threshold,
        nonce,
        ctx=Context(
            accounts={
                "multisig": multisig.pubkey(),
                "rent": RENT,
            },
            pre_instructions=[
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
    multisig_account = await program.account["Multisig"].fetch(multisig.pubkey())
    assert multisig_account.nonce == nonce
    assert multisig_account.threshold == threshold
    assert multisig_account.owners == owners


@async_fixture(scope="module")
async def created_transaction(
    program: Program,
    created_multisig: CreatedMultisig,
) -> CreatedTransaction:
    owner_d = Keypair()
    multisig, _, owners, _, multisig_signer, owner_a, _ = created_multisig
    accounts = [
        program.type["TransactionAccount"](
            pubkey=multisig.pubkey(),
            is_writable=True,
            is_signer=False,
        ),
        program.type["TransactionAccount"](
            pubkey=multisig_signer,
            is_writable=False,
            is_signer=True,
        ),
    ]
    new_owners = [*owners[:2], owner_d.pubkey()]
    data = program.coder.instruction.encode("set_owners", {"owners": new_owners})
    transaction = Keypair()
    tx_size = 1000
    await program.rpc["create_transaction"](
        program.program_id,
        accounts,
        data,
        ctx=Context(
            accounts={
                "multisig": multisig.pubkey(),
                "transaction": transaction.pubkey(),
                "proposer": owner_a.pubkey(),
                "rent": RENT,
            },
            pre_instructions=[
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
    tx_account = await program.account["Transaction"].fetch(transaction.pubkey())
    assert tx_account.program_id == program.program_id
    assert tx_account.accounts == accounts
    assert tx_account.data == data
    assert tx_account.multisig == multisig.pubkey()
    assert tx_account.did_execute is False


@async_fixture(scope="module")
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
                "multisig": multisig.pubkey(),
                "transaction": transaction.pubkey(),
                "owner": owner_b.pubkey(),
            },
            signers=[owner_b],
        ),
    )
    remaining_accounts_raw = program.instruction["set_owners"].accounts(
        {"multisig": multisig.pubkey(), "multisig_signer": multisig_signer}
    )
    with_corrected_signer = []
    for meta in remaining_accounts_raw:
        to_append = (
            AccountMeta(
                pubkey=meta.pubkey, is_signer=False, is_writable=meta.is_writable
            )
            if meta.pubkey == multisig_signer
            else meta
        )
        with_corrected_signer.append(to_append)
    remaining_accounts = with_corrected_signer + [
        AccountMeta(pubkey=program.program_id, is_signer=False, is_writable=False)
    ]
    ctx = Context(
        accounts={
            "multisig": multisig.pubkey(),
            "multisig_signer": multisig_signer,
            "transaction": transaction.pubkey(),
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
    multisig_account = await program.account["Multisig"].fetch(multisig.pubkey())
    assert multisig_account.nonce == nonce
    assert multisig_account.threshold == threshold
    assert multisig_account.owners == new_owners
