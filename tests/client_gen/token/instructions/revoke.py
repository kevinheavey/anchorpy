from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from ..program_id import PROGRAM_ID


class RevokeAccounts(typing.TypedDict):
    source: PublicKey
    owner: PublicKey


def revoke(
    accounts: RevokeAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["source"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b'\xaa\x17\x1f"\x85\xad]\xf2'
    encoded_args = b""
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
