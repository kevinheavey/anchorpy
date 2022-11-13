from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UiAmountToAmountArgs(typing.TypedDict):
    ui_amount: str


layout = borsh.CStruct(borsh.String)


class UiAmountToAmountAccounts(typing.TypedDict):
    mint: PublicKey


def ui_amount_to_amount(
    args: UiAmountToAmountArgs,
    accounts: UiAmountToAmountAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=False)
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xad\xf3@\x04g\x1f84"
    encoded_args = layout.build(
        {
            "ui_amount": args["ui_amount"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
