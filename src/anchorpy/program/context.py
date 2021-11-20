"""This module contains code handling the Context object."""
from dataclasses import dataclass, field
from typing import Any, Tuple, Optional, Dict, List

from solana.keypair import Keypair
from solana.rpc.types import TxOpts
from solana.transaction import AccountMeta
from solana.transaction import TransactionInstruction

from anchorpy.idl import _IdlInstruction
from anchorpy.error import ArgsError


# should be Dict[str, Union[PublicKey, Accounts]]
# but mypy doesn't support recursive types
Accounts = Dict[str, Any]


@dataclass
class Context:
    """Context provides all non-argument inputs for generating Anchor transactions.

    Attributes:
        accounts: The accounts used in the instruction context.
        remaining_accounts: All accounts to pass into an instruction *after* the main
        `accounts`. This can be used for optional or otherwise unknown accounts.
        signers: Accounts that must sign a given transaction.
        pre_instructions: Instructions to run *before* a given method. Often this is
            used, for example to create accounts prior to executing a method.
        post_instructions: Instructions to run *after* a given method. Often this is
            used, for example to close accounts prior to executing a method.
        options: Commitment parameters to use for a transaction.

    """

    # For some reason mkdocstrings doesn't understand the full type hint
    # here if we use list[TransactionInstruction] instead of typing.List.
    # Weirdly there are other places where it understands list[whatever].

    accounts: Accounts = field(default_factory=dict)
    remaining_accounts: List[AccountMeta] = field(default_factory=list)
    signers: List[Keypair] = field(default_factory=list)
    pre_instructions: List[TransactionInstruction] = field(default_factory=list)
    post_instructions: List[TransactionInstruction] = field(default_factory=list)
    options: Optional[TxOpts] = None


def _check_args_length(
    idl_ix: _IdlInstruction,
    args: Tuple,
) -> None:
    """Check that the correct number of args is passed to the RPC function.

    Args:
        idl_ix: The IDL instruction object.
        args: The instruction arguments.

    Raises:
        ArgsError: If the correct number of args is not parsed.
    """
    if len(args) != len(idl_ix.args):
        expected_arg_names = [arg.name for arg in idl_ix.args]
        raise ArgsError(
            f"Provided incorrect number of args to instruction={idl_ix.name}. "
            f"Expected {expected_arg_names}",
            f"Received {args}",
        )


EMPTY_CONTEXT = Context()
