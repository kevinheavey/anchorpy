from __future__ import annotations

import typing

import borsh_construct as borsh
from anchorpy.borsh_extension import BorshPubkey
from solana.publickey import PublicKey
from solana.transaction import AccountMeta, TransactionInstruction

from ..program_id import PROGRAM_ID


class InitializeAccount3Args(typing.TypedDict):
    owner: PublicKey


layout = borsh.CStruct("owner" / BorshPubkey)


class InitializeAccount3Accounts(typing.TypedDict):
    account: PublicKey
    mint: PublicKey


def initialize_account3(
    args: InitializeAccount3Args,
    accounts: InitializeAccount3Accounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
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
    return TransactionInstruction(keys, program_id, data)
