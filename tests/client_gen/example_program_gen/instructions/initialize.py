from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.system_program import SYS_PROGRAM_ID
from solana.sysvar import SYSVAR_RENT_PUBKEY, SYSVAR_CLOCK_PUBKEY
from solana.transaction import TransactionInstruction, AccountMeta
from ..program_id import PROGRAM_ID


class InitializeAccounts(typing.TypedDict):
    state: PublicKey
    payer: PublicKey


def initialize(
    accounts: InitializeAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYSVAR_CLOCK_PUBKEY, is_signer=False, is_writable=False),
        AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xaf\xafm\x1f\r\x98\x9b\xed"
    encoded_args = b""
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
