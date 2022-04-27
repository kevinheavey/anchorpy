import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID
class SetupGameArgs(typing.TypedDict):
    player_two: PublicKey
layout = borsh.CStruct("player_two" / _BorshPubkey)
class SetupGameAccounts(typing.TypedDict):
    game: PublicKey
    player_one: PublicKey
    system_program: PublicKey
def setup_game(args: SetupGameArgs, accounts: SetupGameAccounts) -> TransactionInstruction:
    keys = [AccountMeta(pubkey=accounts["game"], is_signer=True, is_writable=True),AccountMeta(pubkey=accounts["player_one"], is_signer=True, is_writable=True),AccountMeta(pubkey=accounts["system_program"], is_signer=False, is_writable=False)]
    identifier = b'\xb4\xda\x80K:\xde#R'
    encoded_args = layout.build({"player_two": args["player_two"],})
    data = identifier + encoded_args
    return TransactionInstruction(data, keys, PROGRAM_ID)