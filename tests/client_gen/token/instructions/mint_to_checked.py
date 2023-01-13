from __future__ import annotations

import typing

import borsh_construct as borsh
from solana.publickey import PublicKey
from solana.transaction import AccountMeta, TransactionInstruction

from ..program_id import PROGRAM_ID


class MintToCheckedArgs(typing.TypedDict):
    amount: int
    decimals: int


layout = borsh.CStruct("amount" / borsh.U64, "decimals" / borsh.U8)


class MintToCheckedAccounts(typing.TypedDict):
    mint: PublicKey
    account: PublicKey
    owner: PublicKey


def mint_to_checked(
    args: MintToCheckedArgs,
    accounts: MintToCheckedAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["account"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xe5\xec$\xf0v\xe1-}"
    encoded_args = layout.build(
        {
            "amount": args["amount"],
            "decimals": args["decimals"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
