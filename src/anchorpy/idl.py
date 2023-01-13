"""Contains code for parsing the IDL file."""
from typing import Sequence, TypedDict

import solders.pubkey
from anchorpy_core.idl import IdlTypeDefinition
from borsh_construct import U8, CStruct, Vec

from anchorpy.borsh_extension import BorshPubkey


def _idl_address(program_id: solders.pubkey.Pubkey) -> solders.pubkey.Pubkey:
    """Deterministic IDL address as a function of the program id.

    Args:
        program_id: The program ID.

    Returns:
        The public key of the IDL.
    """
    base = solders.pubkey.Pubkey.find_program_address([], program_id)[0]
    return solders.pubkey.Pubkey.create_with_seed(base, "anchor:idl", program_id)


class IdlProgramAccount(TypedDict):
    """The on-chain account of the IDL."""

    authority: solders.pubkey.Pubkey
    data: bytes


IDL_ACCOUNT_LAYOUT = CStruct("authority" / BorshPubkey, "data" / Vec(U8))


def _decode_idl_account(data: bytes) -> IdlProgramAccount:
    """Decode on-chain IDL.

    Args:
        data: binary data from the account that stores the IDL.

    Returns:
        Decoded IDL.
    """
    return IDL_ACCOUNT_LAYOUT.parse(data)


TypeDefs = Sequence[IdlTypeDefinition]
