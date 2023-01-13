from __future__ import annotations

import typing

import borsh_construct as borsh
from anchorpy.borsh_extension import BorshPubkey, COption
from solana.publickey import PublicKey
from solana.transaction import AccountMeta, TransactionInstruction

from ..program_id import PROGRAM_ID


class InitializeMint2Args(typing.TypedDict):
    decimals: int
    mint_authority: PublicKey
    freeze_authority: typing.Optional[PublicKey]


layout = borsh.CStruct(
    "decimals" / borsh.U8,
    "mint_authority" / BorshPubkey,
    "freeze_authority" / COption(BorshPubkey),
)


class InitializeMint2Accounts(typing.TypedDict):
    mint: PublicKey


def initialize_mint2(
    args: InitializeMint2Args,
    accounts: InitializeMint2Accounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=True)
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"_l\xc6\xd2H\xf3\x8f\xeb"
    encoded_args = layout.build(
        {
            "decimals": args["decimals"],
            "mint_authority": args["mint_authority"],
            "freeze_authority": args["freeze_authority"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
