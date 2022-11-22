"""Common utilities."""
from dataclasses import dataclass
from typing import Dict, Any, Union, Tuple, NamedTuple, cast
from construct import Container

from solana.publickey import PublicKey
from anchorpy_core.idl import (
    IdlAccounts,
    IdlInstruction,
    IdlAccountItem,
)
from pyheck import snake
from anchorpy.program.context import Accounts

AddressType = Union[PublicKey, str]


class Event(NamedTuple):
    """A parsed event object."""

    name: str
    data: Any


@dataclass
class Instruction:
    """Container for a named instruction.

    Attributes:
        data: The actual instruction data.
        name: The name of the instruction.
    """

    data: Union[Dict[str, Any], Container[Any]]
    name: str


def _to_instruction(idl_ix: IdlInstruction, args: Tuple) -> Instruction:
    """Convert an IDL instruction and arguments to an Instruction object.

    Args:
        idl_ix: The IDL instruction object.
        args: The instruction arguments.

    Raises:
        ValueError: If the incorrect number of arguments is provided.

    Returns:
        The parsed Instruction object.
    """
    if len(idl_ix.args) != len(args):
        raise ValueError("Invalid argument length")
    ix: Dict[str, Any] = {}
    for idx, ix_arg in enumerate(idl_ix.args):
        ix[snake(ix_arg.name)] = args[idx]
    return Instruction(data=ix, name=snake(idl_ix.name))


def validate_accounts(ix_accounts: list[IdlAccountItem], accounts: Accounts):
    """Check that accounts passed in `ctx` match the IDL.

    Args:
        ix_accounts: Accounts from the IDL.
        accounts: Accounts from the `ctx` arg.

    Raises:
        ValueError: If `ctx` accounts don't match the IDL.
    """
    for acc in ix_accounts:
        acc_name = snake(acc.name)
        if isinstance(acc, IdlAccounts):
            nested = cast(Accounts, accounts[acc_name])
            validate_accounts(acc.accounts, nested)
        elif acc_name not in accounts:
            raise ValueError(f"Invalid arguments: {acc_name} not provided")


def translate_address(address: AddressType) -> PublicKey:
    """Convert `str | PublicKey` into `PublicKey`.

    Args:
        address: Public key as string or `PublicKey`.

    Returns:
        Public key as `PublicKey`.
    """
    if isinstance(address, str):
        return PublicKey(address)
    return address
