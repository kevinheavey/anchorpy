from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.transaction import TransactionInstruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class InitializeAccount2Args(typing.TypedDict):
    owner: PublicKey


layout = borsh.CStruct("owner" / BorshPubkey)


class InitializeAccount2Accounts(typing.TypedDict):
    account: PublicKey
    mint: PublicKey


def initialize_account2(
    args: InitializeAccount2Args,
    accounts: InitializeAccount2Accounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["account"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x08\xb6\x95\x90\xb9\x1f\xd1i"
    encoded_args = layout.build(
        {
            "owner": args["owner"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
