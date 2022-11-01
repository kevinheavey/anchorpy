"""Contains code for parsing the IDL file."""
from typing import TypedDict, Sequence
from anchorpy_core.idl import IdlTypeDefinition

from borsh_construct import CStruct, Vec, U8
import solana.publickey  # noqa: WPS301

from anchorpy.borsh_extension import BorshPubkey


def _idl_address(program_id: solana.publickey.PublicKey) -> solana.publickey.PublicKey:
    """Deterministic IDL address as a function of the program id.

    Args:
        program_id: The program ID.

    Returns:
        The public key of the IDL.
    """
    base = solana.publickey.PublicKey.find_program_address([], program_id)[0]
    return solana.publickey.PublicKey.create_with_seed(base, "anchor:idl", program_id)


class IdlProgramAccount(TypedDict):
    """The on-chain account of the IDL."""

    authority: solana.publickey.PublicKey
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
