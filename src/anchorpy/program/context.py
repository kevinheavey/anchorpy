from dataclasses import dataclass, field
from typing import List, Any, Tuple, Optional, Dict

from solana.keypair import Keypair
from solana.rpc.types import TxOpts
from solana.transaction import AccountMeta, TransactionInstruction

from anchorpy.idl import IdlInstruction


class ArgsError(Exception):
    pass


# should be Dict[str, Union[PublicKey, Accounts]]
# but mypy doesn't support recursive types
Accounts = Dict[str, Any]


@dataclass
class Context:
    """Context provides all non-argument inputs for generating Anchor transactions.

    Args:
        accounts: Accounts used in the instruction context.
        remaining_accounts: All accounts to pass into an instruction *after* the main
        `accounts`. This can be used for optional or otherwise unknown accounts.
        signers: Accounts that must sign a given transaction.
        instructions: Instructions to run *before* a given method. Often this is used,
            for example to create accounts prior to executing a method.
        options: Commitment parameters to use for a transaction.

    """

    accounts: Accounts = field(default_factory=dict)
    remaining_accounts: List[AccountMeta] = field(default_factory=list)
    signers: List[Keypair] = field(default_factory=list)
    instructions: List[TransactionInstruction] = field(default_factory=list)
    options: Optional[TxOpts] = None


def check_args_length(
    idl_ix: IdlInstruction,
    args: Tuple,
) -> None:
    """Check that the correct number of args is passed to the RPC function."""
    if len(args) != len(idl_ix.args):
        raise ArgsError(f"Provided too many args to method={idl_ix.name}")


EMPTY_CONTEXT = Context()
