from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class InitializeMultisigArgs(typing.TypedDict):
    m: int


layout = borsh.CStruct("m" / borsh.U8)


class InitializeMultisigAccounts(typing.TypedDict):
    multisig: PublicKey


def initialize_multisig(
    args: InitializeMultisigArgs,
    accounts: InitializeMultisigAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["multisig"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xdc\x82u\x15\x1b\xe3N\xd5"
    encoded_args = layout.build(
        {
            "m": args["m"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
