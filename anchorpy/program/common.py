from typing import Dict, List, Any, Union

from anchorpy.public_key import PublicKey
from anchorpy.idl import Idl, IdlStateMethod, IdlInstruction, IdlAccountItem

AddressType = Union[PublicKey, str]


def parse_idl_errors(idl: Idl) -> Dict[int, str]:
    """Turns IDL errors into something readable. Uses message if available, otherwise name."""
    errors = dict()
    for e in idl.errors:
        msg = e.msg if e.msg else e.name
        errors[e.code] = msg
    return errors


def to_instruction(idl_ix: Union[IdlInstruction, IdlStateMethod], args: List[Any]):
    if len(idl_ix.args) != len(args):
        raise Exception("Invalid argument length")
    ix: Dict[str, Any] = dict()
    for idx, ix_arg in enumerate(idl_ix.args):
        ix[ix_arg.name] = args[idx]
    return ix


def validate_accounts(ix_accounts: List[IdlAccountItem], accounts):
    for acc in ix_accounts:
        if hasattr(acc, "accounts"):  # TODO: hella hacky
            validate_accounts(acc.accounts, accounts[acc.name])
        else:
            if acc.name not in accounts:
                raise Exception(f"Invalid arguments: {acc.name} not provided")


def translate_address(address: AddressType):
    if isinstance(address, str):
        return PublicKey(address)
    else:
        return address
