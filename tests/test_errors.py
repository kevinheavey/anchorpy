import pytest
from anchorpy.error import ProgramError
from anchorpy.program.core import Program
from anchorpy.workspace import create_workspace
from anchorpy.program.context import Context
from solana.keypair import Keypair
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.transaction import AccountMeta, Transaction, TransactionInstruction
from solana.rpc.core import RPCException


@pytest.mark.integration
@pytest.fixture(scope="session")
def program() -> Program:
    workspace = create_workspace()
    return workspace["errors"]


@pytest.mark.integration
def test_hello_err(program: Program) -> None:
    """Test error from hello func."""
    with pytest.raises(ProgramError) as excinfo:
        program.rpc["hello"]()
    assert excinfo.value.code == 300
    expected_msg = "This is an error message clients will automatically display"
    assert excinfo.value.msg == expected_msg
    assert expected_msg in str(excinfo)


@pytest.mark.integration
def test_hello_no_msg_err(program: Program) -> None:
    """Test error from helloNoMsg func."""
    with pytest.raises(ProgramError) as excinfo:
        program.rpc["helloNoMsg"]()
    assert excinfo.value.msg == "HelloNoMsg"
    assert excinfo.value.code == 300 + 123


@pytest.mark.integration
def test_hello_next_err(program: Program) -> None:
    """Test error from helloNext func."""
    with pytest.raises(ProgramError) as excinfo:
        program.rpc["helloNext"]()
    assert excinfo.value.msg == "HelloNext"
    assert excinfo.value.code == 300 + 124


@pytest.mark.integration
def test_mut_err(program: Program) -> None:
    """Test mmut error."""
    with pytest.raises(ProgramError) as excinfo:
        program.rpc["mutError"](ctx=Context(accounts={"myAccount": SYSVAR_RENT_PUBKEY}))
    assert excinfo.value.msg == "A mut constraint was violated"
    assert excinfo.value.code == 140


@pytest.mark.integration
def test_has_one_err(program: Program) -> None:
    """Test hasOneError."""
    account = Keypair()
    with pytest.raises(ProgramError) as excinfo:
        program.rpc["hasOneError"](
            ctx=Context(
                accounts={
                    "myAccount": account.public_key,
                    "owner": SYSVAR_RENT_PUBKEY,
                    "rent": SYSVAR_RENT_PUBKEY,
                },
                instructions=[
                    program.account["HasOneAccount"].create_instruction(account)
                ],
                signers=[account],
            )
        )
    assert excinfo.value.msg == "A has_one constraint was violated"
    assert excinfo.value.code == 141


@pytest.mark.integration
def test_signer_err(program: Program) -> None:
    """Test signer error."""
    tx = Transaction()
    tx.add(
        TransactionInstruction(
            keys=[
                AccountMeta(
                    pubkey=SYSVAR_RENT_PUBKEY, is_writable=False, is_signer=False
                )
            ],
            program_id=program.program_id,
            data=program.coder.instruction.build({"data": {}, "name": "signerError"}),
        )
    )
    with pytest.raises(RPCException) as excinfo:
        program.provider.send(tx)
    assert (
        excinfo.value.args[0]["message"]
        == "Transaction simulation failed: Error processing "
        "Instruction 0: custom program error: 0x8e"
    )
