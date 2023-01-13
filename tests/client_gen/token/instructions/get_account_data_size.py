from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from ..program_id import PROGRAM_ID


class GetAccountDataSizeAccounts(typing.TypedDict):
    mint: Pubkey


def get_account_data_size(
    accounts: GetAccountDataSizeAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=False)
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x10\xb1\xd2\x80\x15-o\x1f"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
