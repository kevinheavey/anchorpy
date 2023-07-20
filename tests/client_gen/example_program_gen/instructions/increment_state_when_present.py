from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
from ..program_id import PROGRAM_ID


class IncrementStateWhenPresentAccounts(typing.TypedDict):
    first_state: typing.Optional[Pubkey]
    second_state: Pubkey


def increment_state_when_present(
    accounts: IncrementStateWhenPresentAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["first_state"], is_signer=False, is_writable=True)
        if accounts["first_state"]
        else AccountMeta(pubkey=program_id, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["second_state"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xf1!\xdd(\xa3Jy%"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
