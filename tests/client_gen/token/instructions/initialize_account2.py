from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.sysvar import RENT
from solders.instruction import Instruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class InitializeAccount2Args(typing.TypedDict):
    owner: Pubkey


layout = borsh.CStruct("owner" / BorshPubkey)


class InitializeAccount2Accounts(typing.TypedDict):
    account: Pubkey
    mint: Pubkey


def initialize_account2(
    args: InitializeAccount2Args,
    accounts: InitializeAccount2Accounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["account"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x08\xb6\x95\x90\xb9\x1f\xd1i"
    encoded_args = layout.build(
        {
            "owner": args["owner"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
