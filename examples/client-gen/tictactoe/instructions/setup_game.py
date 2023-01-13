from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class SetupGameArgs(typing.TypedDict):
    player_two: Pubkey


layout = borsh.CStruct("player_two" / BorshPubkey)


class SetupGameAccounts(typing.TypedDict):
    game: Pubkey
    player_one: Pubkey


def setup_game(
    args: SetupGameArgs,
    accounts: SetupGameAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["game"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["player_one"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xb4\xda\x80K:\xde#R"
    encoded_args = layout.build(
        {
            "player_two": args["player_two"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
