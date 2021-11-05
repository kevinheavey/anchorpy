"""Common utilities."""
from dataclasses import dataclass
from typing import Dict, List, Any, Union, cast, get_args, Tuple
from construct import Container

from solana.publickey import PublicKey
from anchorpy.idl import (
    Idl,
    IdlAccounts,
    IdlInstruction,
    IdlAccountItem,
)
from anchorpy.program.context import Accounts

AddressType = Union[PublicKey, str]


def parse_idl_errors(idl: Idl) -> Dict[int, str]:
    """Turn IDL errors into something readable.

    Uses message if available, otherwise name.

    Args:
        idl: Parsed `Idl` instance.

    """
    errors = {}
    for e in idl.errors:
        msg = e.msg if e.msg else e.name
        errors[e.code] = msg
    return errors


@dataclass
class Instruction:
    data: Union[Dict[str, Any], Container[Any]]
    name: str


def to_instruction(idl_ix: IdlInstruction, args: Tuple) -> Instruction:
    if len(idl_ix.args) != len(args):
        raise ValueError("Invalid argument length")
    ix: Dict[str, Any] = {}
    for idx, ix_arg in enumerate(idl_ix.args):
        ix[ix_arg.name] = args[idx]
    return Instruction(data=ix, name=idl_ix.name)


def validate_accounts(ix_accounts: List[IdlAccountItem], accounts: Accounts):
    """Check that accounts passed in `ctx` match the IDL.

    Args:
        ix_accounts: Accounts from the IDL.
        accounts: Accounts from the `ctx` arg.

    Raises:
        ValueError: If `ctx` accounts don't match the IDL.
    """
    for acc in ix_accounts:
        if isinstance(acc, get_args(IdlAccounts)):
            idl_accounts = cast(IdlAccounts, acc)
            validate_accounts(idl_accounts.accounts, accounts[acc.name])
        elif acc.name not in accounts:
            raise ValueError(f"Invalid arguments: {acc.name} not provided")


def translate_address(address: AddressType):
    """Convert `str | PublicKey` into `PublicKey`.

    Args:
        address: Public key as string or `PublicKey`.

    Returns:
        Public key as `PublicKey`.
    """
    if isinstance(address, str):
        return PublicKey(address)
    return address
