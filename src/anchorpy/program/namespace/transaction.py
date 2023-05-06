"""This module deals with generating transactions."""
from typing import Any, Protocol

from anchorpy_core.idl import IdlInstruction
from more_itertools import unique_everseen
from solders.hash import Hash
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.transaction import VersionedTransaction

from anchorpy.program.context import EMPTY_CONTEXT, Context, _check_args_length
from anchorpy.program.namespace.instruction import _InstructionFn


class _TransactionFn(Protocol):
    """A function to create a `Transaction` for a given program instruction."""

    def __call__(
        self, *args: Any, payer: Keypair, blockhash: Hash, ctx: Context = EMPTY_CONTEXT
    ) -> VersionedTransaction:
        """Make sure that the function looks like this.

        Args:
            *args: The positional arguments for the program. The type and number
                of these arguments depend on the program being used.
            payer: The transaction fee payer.
            blockhash: A recent blockhash.
            ctx: non-argument parameters to pass to the method.

        """
        ...


# ts TransactionNamespaceFactory.build
def _build_transaction_fn(
    idl_ix: IdlInstruction, ix_fn: _InstructionFn
) -> _TransactionFn:
    """Build the function that generates Transaction objects.

    Args:
        idl_ix: Instruction item from the IDL.
        ix_fn (_InstructionFn): The function that generates instructions.

    Returns:
        _TransactionFn: [description]
    """

    def tx_fn(
        *args: Any, payer: Keypair, blockhash: Hash, ctx: Context = EMPTY_CONTEXT
    ) -> VersionedTransaction:
        ixns: list[Instruction] = []
        _check_args_length(idl_ix, args)
        if ctx.pre_instructions:
            ixns.extend(ctx.pre_instructions)
        ixns.append(ix_fn(*args, ctx=ctx))
        if ctx.post_instructions:
            ixns.extend(ctx.post_instructions)
        ctx_signers = ctx.signers
        signers = [] if ctx_signers is None else ctx_signers
        all_signers = list(unique_everseen([payer, *signers]))
        msg = Message.new_with_blockhash(ixns, payer.pubkey(), blockhash)
        return VersionedTransaction(msg, all_signers)

    return tx_fn
