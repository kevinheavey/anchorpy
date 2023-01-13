from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class ApproveCheckedArgs(typing.TypedDict):
    amount: int
    decimals: int


layout = borsh.CStruct("amount" / borsh.U64, "decimals" / borsh.U8)


class ApproveCheckedAccounts(typing.TypedDict):
    source: Pubkey
    mint: Pubkey
    delegate: Pubkey
    owner: Pubkey


def approve_checked(
    args: ApproveCheckedArgs,
    accounts: ApproveCheckedAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["source"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["delegate"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"/\xc5\xfe*:\xc9:m"
    encoded_args = layout.build(
        {
            "amount": args["amount"],
            "decimals": args["decimals"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
