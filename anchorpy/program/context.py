from dataclasses import dataclass, field
from typing import List, Any, Tuple, Dict, Union

from solana.account import Account
from solana.rpc.types import TxOpts
from solana.transaction import AccountMeta, TransactionInstruction

from anchorpy.program.common import AddressType
from anchorpy.idl import IdlInstruction


class ArgsError(Exception):
    pass


Accounts = Dict[str, Union[AddressType, AccountMeta]]


@dataclass
class Context:
    accounts: Accounts = field(default_factory=list)
    remaining_accounts: List[AccountMeta] = field(default_factory=list)
    signers: List[Account] = field(default_factory=list)
    instructions: List[TransactionInstruction] = field(default_factory=list)
    options: TxOpts = None


def split_args_and_context(idl_ix: IdlInstruction, args: List[Any]) -> Tuple[List[Any], Context]:
    options = dict()
    new_args = args
    if len(args) > len(idl_ix.args):
        if len(args) != len(idl_ix.args) + 1:
            raise ArgsError(f"Provided too many args to method={idl_ix.name}")
        new_args = list(args)
        options = new_args.pop()
    return new_args, Context(**options)
