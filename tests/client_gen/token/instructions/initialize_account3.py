from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class InitializeAccount3Args(typing.TypedDict):
    owner: Pubkey


layout = borsh.CStruct("owner" / BorshPubkey)


class InitializeAccount3Accounts(typing.TypedDict):
    account: Pubkey
    mint: Pubkey


def initialize_account3(
    args: InitializeAccount3Args,
    accounts: InitializeAccount3Accounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["account"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x17\x8e\x8c\x87\x15\xa0\x85@"
    encoded_args = layout.build(
        {
            "owner": args["owner"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
