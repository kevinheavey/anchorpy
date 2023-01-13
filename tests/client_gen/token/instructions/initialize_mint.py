from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.sysvar import RENT
from solders.instruction import Instruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey, COption
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class InitializeMintArgs(typing.TypedDict):
    decimals: int
    mint_authority: Pubkey
    freeze_authority: typing.Optional[Pubkey]


layout = borsh.CStruct(
    "decimals" / borsh.U8,
    "mint_authority" / BorshPubkey,
    "freeze_authority" / COption(BorshPubkey),
)


class InitializeMintAccounts(typing.TypedDict):
    mint: Pubkey


def initialize_mint(
    args: InitializeMintArgs,
    accounts: InitializeMintAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xd1*\xc3\x04\x81U\xd1,"
    encoded_args = layout.build(
        {
            "decimals": args["decimals"],
            "mint_authority": args["mint_authority"],
            "freeze_authority": args["freeze_authority"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
