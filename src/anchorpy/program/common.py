from typing import Dict, List, Any, Union, cast, get_args, TypedDict, Tuple

from solana.publickey import PublicKey
from anchorpy.idl import (
    Idl,
    IdlAccounts,
    IdlInstruction,
    IdlAccountItem,
)

AddressType = Union[PublicKey, str]


def parse_idl_errors(idl: Idl) -> Dict[int, str]:
    """Turns IDL errors into something readable.

    Uses message if available, otherwise name."""
    errors = {}
    for e in idl.errors:
        msg = e.msg if e.msg else e.name
        errors[e.code] = msg
    return errors


class Instruction(TypedDict):
    data: Dict[str, Any]
    name: str


def to_instruction(idl_ix: IdlInstruction, args: Tuple) -> Instruction:
    if len(idl_ix.args) != len(args):
        raise ValueError("Invalid argument length")
    ix: Dict[str, Any] = {}
    for idx, ix_arg in enumerate(idl_ix.args):
        ix[ix_arg.name] = args[idx]
    return Instruction(data=ix, name=idl_ix.name)


def validate_accounts(ix_accounts: List[IdlAccountItem], accounts):
    for acc in ix_accounts:
        if isinstance(acc, get_args(IdlAccounts)):
            idl_accounts = cast(IdlAccounts, acc)
            validate_accounts(idl_accounts.accounts, accounts[acc.name])
        elif acc.name not in accounts:
            raise ValueError(f"Invalid arguments: {acc.name} not provided")


def translate_address(address: AddressType):
    if isinstance(address, str):
        return PublicKey(address)
    return address
