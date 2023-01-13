from __future__ import annotations

import typing

import borsh_construct as borsh
from solana.publickey import PublicKey
from solana.transaction import AccountMeta, TransactionInstruction

from ..program_id import PROGRAM_ID


class TransferCheckedArgs(typing.TypedDict):
    amount: int
    decimals: int


layout = borsh.CStruct("amount" / borsh.U64, "decimals" / borsh.U8)


class TransferCheckedAccounts(typing.TypedDict):
    source: PublicKey
    mint: PublicKey
    destination: PublicKey
    authority: PublicKey


def transfer_checked(
    args: TransferCheckedArgs,
    accounts: TransferCheckedAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["source"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["destination"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"w\xfa\xca\x18\xfd\x87\xf4y"
    encoded_args = layout.build(
        {
            "amount": args["amount"],
            "decimals": args["decimals"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
