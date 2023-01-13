"""Mimics anchor/tests/errors/tests/errors.js."""
from anchorpy import Context, Program
from anchorpy.error import ProgramError
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType
from pytest import fixture, mark, raises
from solders.keypair import Keypair
from solana.rpc.core import RPCException
from solders.sysvar import RENT
from solders.instruction import AccountMeta, Instruction
from solana.transaction import Transaction

workspace = workspace_fixture(
    "anchor/tests/errors/", build_cmd="anchor build --skip-lint"
)


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    return workspace["errors"]


@mark.asyncio
async def test_hello_err(program: Program) -> None:
    """Test error from hello func."""
    with raises(ProgramError) as excinfo:
        await program.rpc["hello"]()
    assert excinfo.value.code == 6000
    expected_msg = "This is an error message clients will automatically display"
    assert excinfo.value.msg == expected_msg
    assert expected_msg in str(excinfo)
    assert excinfo.value.logs


@mark.asyncio
async def test_hello_no_msg_err(program: Program) -> None:
    """Test error from helloNoMsg func."""
    with raises(ProgramError) as excinfo:
        await program.rpc["hello_no_msg"]()
    assert excinfo.value.msg == "HelloNoMsg"
    assert excinfo.value.code == 6000 + 123
    assert excinfo.value.logs


@mark.asyncio
async def test_hello_next_err(program: Program) -> None:
    """Test error from helloNext func."""
    with raises(ProgramError) as excinfo:
        await program.rpc["hello_next"]()
    assert excinfo.value.msg == "HelloNext"
    assert excinfo.value.code == 6000 + 124
    assert excinfo.value.logs


@mark.asyncio
async def test_mut_err(program: Program) -> None:
    """Test mmut error."""
    with raises(ProgramError) as excinfo:
        await program.rpc["mut_error"](ctx=Context(accounts={"my_account": RENT}))
    assert excinfo.value.msg == "A mut constraint was violated"
    assert excinfo.value.code == 2000
    assert excinfo.value.logs


@mark.asyncio
async def test_has_one_err(program: Program) -> None:
    """Test hasOneError."""
    account = Keypair()
    with raises(ProgramError) as excinfo:
        await program.rpc["has_one_error"](
            ctx=Context(
                accounts={
                    "my_account": account.pubkey(),
                    "owner": RENT,
                    "rent": RENT,
                },
                pre_instructions=[
                    await program.account["HasOneAccount"].create_instruction(account)
                ],
                signers=[account],
            )
        )
    assert excinfo.value.msg == "A has_one constraint was violated"
    assert excinfo.value.code == 2001
    assert excinfo.value.logs


@mark.asyncio
async def test_signer_err(program: Program) -> None:
    """Test signer error."""
    tx = Transaction()
    tx.add(
        Instruction(
            keys=[
                AccountMeta(
                    pubkey=RENT,
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
        excinfo.value.args[0].message
        == "Transaction simulation failed: Error processing "
        "Instruction 0: custom program error: 0xbc2"
    )


@mark.asyncio
async def test_raw_custom_err(program: Program) -> None:
    with raises(ProgramError) as excinfo:
        await program.rpc["raw_custom_error"](
            ctx=Context(
                accounts={
                    "my_account": RENT,
                },
            )
        )
    assert excinfo.value.msg == "HelloCustom"
    assert excinfo.value.code == 6000 + 125
    assert excinfo.value.logs


@mark.asyncio
async def test_account_not_initialised_err(program: Program) -> None:
    with raises(ProgramError) as excinfo:
        await program.rpc["account_not_initialized_error"](
            ctx=Context(
                accounts={
                    "not_initialized_account": Keypair().pubkey(),
                },
            )
        )
    assert (
        excinfo.value.msg
        == "The program expected this account to be already initialized"
    )
    assert excinfo.value.code == 3012
    assert excinfo.value.logs
