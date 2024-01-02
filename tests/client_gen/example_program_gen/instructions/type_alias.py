from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class TypeAliasArgs(typing.TypedDict):
    u8_array: types.u8_array.U8Array


layout = borsh.CStruct("u8_array" / borsh.U8[8])


def type_alias(
    args: TypeAliasArgs,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = []
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"5\x84\x11\xf9y\xc216"
    encoded_args = layout.build(
        {
            "u8_array": args["u8_array"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
