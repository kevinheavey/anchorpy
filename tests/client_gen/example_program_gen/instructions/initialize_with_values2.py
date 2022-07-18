from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from construct import Construct
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class InitializeWithValues2Args(typing.TypedDict):
    vec_of_option: list[typing.Optional[int]]


layout = borsh.CStruct(
    "vec_of_option" / borsh.Vec(typing.cast(Construct, borsh.Option(borsh.U64)))
)


class InitializeWithValues2Accounts(typing.TypedDict):
    state: PublicKey
    payer: PublicKey
    system_program: PublicKey


def initialize_with_values2(
    args: InitializeWithValues2Args,
    accounts: InitializeWithValues2Accounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(
            pubkey=accounts["system_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xf8\xbe\x15a\xef\x94'\xb5"
    encoded_args = layout.build(
        {
            "vec_of_option": args["vec_of_option"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
