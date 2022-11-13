from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.system_program import SYS_PROGRAM_ID
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class InitMyAccountArgs(typing.TypedDict):
    seed_a: int


layout = borsh.CStruct("seed_a" / borsh.U8)
NESTED_NESTED_ACCOUNT_NESTED = PublicKey.find_program_address(
    seeds=[
        b"nested-seed",
        b"test",
        b"hi",
        b"hi",
        b"\x01",
        b"\x02\x00\x00\x00",
        b"\x03\x00\x00\x00\x00\x00\x00\x00",
    ],
    program_id=PROGRAM_ID,
)[0]
INIT_MY_ACCOUNT_ACCOUNTS_ACCOUNT = PublicKey.find_program_address(
    seeds=[
        b"another-seed",
        b"test",
        b"hi",
        b"hi",
        b"\x01",
        b"\x02\x00\x00\x00",
        b"\x03\x00\x00\x00\x00\x00\x00\x00",
    ],
    program_id=PROGRAM_ID,
)[0]


class InitMyAccountAccounts(typing.TypedDict):
    base: PublicKey
    base2: PublicKey
    nested: NestedNested


def init_my_account(
    args: InitMyAccountArgs,
    accounts: InitMyAccountAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["base"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["base2"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=INIT_MY_ACCOUNT_ACCOUNTS_ACCOUNT, is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=NESTED_NESTED_ACCOUNT_NESTED, is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b" ;\x05\xcd^E\xe3z"
    encoded_args = layout.build(
        {
            "seed_a": args["seed_a"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
