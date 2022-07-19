from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from ..program_id import PROGRAM_ID


class InitializeAccounts(typing.TypedDict):
    state: PublicKey
    nested: NestedNested
    payer: PublicKey
    system_program: PublicKey


class NestedNested(typing.TypedDict):
    clock: PublicKey
    rent: PublicKey


def initialize(
    accounts: InitializeAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=True, is_writable=True),
        AccountMeta(
            pubkey=accounts["nested"]["clock"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["nested"]["rent"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(
            pubkey=accounts["system_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xaf\xafm\x1f\r\x98\x9b\xed"
    encoded_args = b""
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
