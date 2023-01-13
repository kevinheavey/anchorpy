from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class InitializeMultisig2Args(typing.TypedDict):
    m: int


layout = borsh.CStruct("m" / borsh.U8)


class InitializeMultisig2Accounts(typing.TypedDict):
    multisig: Pubkey
    signer: Pubkey


def initialize_multisig2(
    args: InitializeMultisig2Args,
    accounts: InitializeMultisig2Accounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["multisig"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["signer"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"Q\xefI'\x1b\x94\x02\x92"
    encoded_args = layout.build(
        {
            "m": args["m"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
