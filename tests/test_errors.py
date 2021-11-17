"""Mimics anchor/tests/errors/tests/errors.js."""
from pathlib import Path
from typing import AsyncGenerator
from pytest import raises, mark, fixture
from anchorpy import ProgramError, Program, create_workspace, close_workspace, Context
from solana.keypair import Keypair
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.transaction import AccountMeta, Transaction, TransactionInstruction
from solana.rpc.core import RPCException
from anchorpy.pytest_plugin import get_localnet

PATH = Path("anchor/tests/errors/")

localnet = get_localnet(PATH)


@fixture(scope="module")
async def program(localnet) -> AsyncGenerator[Program, None]:
    workspace = create_workspace(PATH)
    yield workspace["errors"]
    await close_workspace(workspace)


@mark.asyncio
async def test_hello_err(program: Program) -> None:
    """Test error from hello func."""
    with raises(ProgramError) as excinfo:
        await program.rpc["hello"]()
    assert excinfo.value.code == 300
    expected_msg = "This is an error message clients will automatically display"
    assert excinfo.value.msg == expected_msg
    assert expected_msg in str(excinfo)


@mark.asyncio
async def test_hello_no_msg_err(program: Program) -> None:
    """Test error from helloNoMsg func."""
    with raises(ProgramError) as excinfo:
        await program.rpc["hello_no_msg"]()
    assert excinfo.value.msg == "HelloNoMsg"
    assert excinfo.value.code == 300 + 123


@mark.asyncio
async def test_hello_next_err(program: Program) -> None:
    """Test error from helloNext func."""
    with raises(ProgramError) as excinfo:
        await program.rpc["hello_next"]()
    assert excinfo.value.msg == "HelloNext"
    assert excinfo.value.code == 300 + 124


@mark.asyncio
async def test_mut_err(program: Program) -> None:
    """Test mmut error."""
    with raises(ProgramError) as excinfo:
        await program.rpc["mut_error"](
            ctx=Context(accounts={"my_account": SYSVAR_RENT_PUBKEY})
        )
    assert excinfo.value.msg == "A mut constraint was violated"
    assert excinfo.value.code == 140


@mark.asyncio
async def test_has_one_err(program: Program) -> None:
    """Test hasOneError."""
    account = Keypair()
    with raises(ProgramError) as excinfo:
        await program.rpc["has_one_error"](
            ctx=Context(
                accounts={
                    "my_account": account.public_key,
                    "owner": SYSVAR_RENT_PUBKEY,
                    "rent": SYSVAR_RENT_PUBKEY,
                },
                instructions=[
                    await program.account["HasOneAccount"].create_instruction(account)
                ],
                signers=[account],
            )
        )
    assert excinfo.value.msg == "A has_one constraint was violated"
    assert excinfo.value.code == 141


@mark.asyncio
async def test_signer_err(program: Program) -> None:
    """Test signer error."""
    tx = Transaction()
    tx.add(
        TransactionInstruction(
            keys=[
                AccountMeta(
                    pubkey=SYSVAR_RENT_PUBKEY,
                    is_writable=False,
                    is_signer=False,
                ),
            ],
            program_id=program.program_id,
            data=program.coder.instruction.encode("signer_error", {}),
        ),
    )
    with raises(RPCException) as excinfo:
        await program.provider.send(tx)
    assert (
        excinfo.value.args[0]["message"]
        == "Transaction simulation failed: Error processing "
        "Instruction 0: custom program error: 0x8e"
    )
