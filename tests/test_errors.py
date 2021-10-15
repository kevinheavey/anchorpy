import pytest
from anchorpy.error import ProgramError
from anchorpy.workspace import create_workspace
from anchorpy.program.context import Context
from solana.keypair import Keypair
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.transaction import AccountMeta, Transaction, TransactionInstruction
from solana.rpc.core import RPCException

workspace = create_workspace()
program = workspace["errors"]
provider = program.provider


def test() -> None:
    with pytest.raises(ProgramError) as excinfo:
        program.rpc["hello"]()
    assert excinfo.value.code == 300
    expected_msg = "This is an error message clients will automatically display"
    assert excinfo.value.msg == expected_msg
    assert expected_msg in str(excinfo)

    with pytest.raises(ProgramError) as excinfo:
        program.rpc["helloNoMsg"]()
    assert excinfo.value.msg == "HelloNoMsg"
    assert excinfo.value.code == 300 + 123

    with pytest.raises(ProgramError) as excinfo:
        program.rpc["helloNext"]()
    assert excinfo.value.msg == "HelloNext"
    assert excinfo.value.code == 300 + 124

    with pytest.raises(ProgramError) as excinfo:
        program.rpc["mutError"](ctx=Context(accounts={"myAccount": SYSVAR_RENT_PUBKEY}))
    assert excinfo.value.msg == "A mut constraint was violated"
    assert excinfo.value.code == 140

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

    account = Keypair()
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
