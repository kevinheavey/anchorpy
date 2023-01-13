from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.sysvar import RENT
from solders.instruction import Instruction, AccountMeta
from ..program_id import PROGRAM_ID


class InitializeAccountAccounts(typing.TypedDict):
    account: Pubkey
    mint: Pubkey
    owner: Pubkey


def initialize_account(
    accounts: InitializeAccountAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["account"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["owner"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"Jsc]\xc5Eg\x07"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
