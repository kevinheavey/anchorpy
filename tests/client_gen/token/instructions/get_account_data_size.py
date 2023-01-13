from __future__ import annotations

import typing

from solana.publickey import PublicKey
from solana.transaction import AccountMeta, TransactionInstruction

from ..program_id import PROGRAM_ID


class GetAccountDataSizeAccounts(typing.TypedDict):
    mint: PublicKey


def get_account_data_size(
    accounts: GetAccountDataSizeAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=False)
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x10\xb1\xd2\x80\x15-o\x1f"
    encoded_args = b""
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
