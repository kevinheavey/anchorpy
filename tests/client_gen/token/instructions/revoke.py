from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from ..program_id import PROGRAM_ID


class RevokeAccounts(typing.TypedDict):
    source: Pubkey
    owner: Pubkey


def revoke(
    accounts: RevokeAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["source"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b'\xaa\x17\x1f"\x85\xad]\xf2'
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
