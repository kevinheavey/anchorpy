from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.sysvar import RENT
from solders.instruction import Instruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class CreateArgs(typing.TypedDict):
    authority: Pubkey


layout = borsh.CStruct("authority" / BorshPubkey)


class CreateAccounts(typing.TypedDict):
    counter: Pubkey


def create(
    args: CreateArgs,
    accounts: CreateAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["counter"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x18\x1e\xc8(\x05\x1c\x07w"
    encoded_args = layout.build(
        {
            "authority": args["authority"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
