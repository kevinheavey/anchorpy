from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class BurnCheckedArgs(typing.TypedDict):
    amount: int
    decimals: int


layout = borsh.CStruct("amount" / borsh.U64, "decimals" / borsh.U8)


class BurnCheckedAccounts(typing.TypedDict):
    account: Pubkey
    mint: Pubkey
    authority: Pubkey


def burn_checked(
    args: BurnCheckedArgs,
    accounts: BurnCheckedAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["account"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xc6y\xc8fx\xd0\x9b\xb2"
    encoded_args = layout.build(
        {
            "amount": args["amount"],
            "decimals": args["decimals"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
