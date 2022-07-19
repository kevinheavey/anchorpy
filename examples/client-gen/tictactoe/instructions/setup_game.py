from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class SetupGameArgs(typing.TypedDict):
    player_two: PublicKey


layout = borsh.CStruct("player_two" / BorshPubkey)


class SetupGameAccounts(typing.TypedDict):
    game: PublicKey
    player_one: PublicKey
    system_program: PublicKey


def setup_game(
    args: SetupGameArgs,
    accounts: SetupGameAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["game"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["player_one"], is_signer=True, is_writable=True),
        AccountMeta(
            pubkey=accounts["system_program"], is_signer=False, is_writable=False
        ),
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
    return TransactionInstruction(keys, program_id, data)
