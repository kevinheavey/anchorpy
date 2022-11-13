from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class SetAuthorityArgs(typing.TypedDict):
    authority_type: types.authority_type.AuthorityTypeKind
    new_authority: typing.Optional[Pubkey]


layout = borsh.CStruct(
    "authority_type" / types.authority_type.layout,
    "new_authority" / borsh.COption(BorshPubkey),
)


class SetAuthorityAccounts(typing.TypedDict):
    owned: PublicKey
    owner: PublicKey
    signer: PublicKey


def set_authority(
    args: SetAuthorityArgs,
    accounts: SetAuthorityAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["owned"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["signer"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x85\xfa%\x15n\xa3\x1ay"
    encoded_args = layout.build(
        {
            "authority_type": args["authority_type"].to_encodable(),
            "new_authority": args["new_authority"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
