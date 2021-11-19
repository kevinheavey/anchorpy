"""This module deals with generating transactions."""
from typing import Any, Protocol

from solana.transaction import Transaction

from anchorpy.program.context import EMPTY_CONTEXT, Context, _check_args_length
from anchorpy.idl import _IdlInstruction
from anchorpy.program.namespace.instruction import _InstructionFn


class _TransactionFn(Protocol):
    """A function to create a `Transaction` for a given program instruction."""

    def __call__(self, *args: Any, ctx: Context = EMPTY_CONTEXT) -> Transaction:
        """Make sure that the function looks like this.

        Args:
            *args: The positional arguments for the program. The type and number
                of these arguments depend on the program being used.
            ctx: non-argument parameters to pass to the method.

        """
        ...


# ts TransactionNamespaceFactory.build
def _build_transaction_fn(
    idl_ix: _IdlInstruction, ix_fn: _InstructionFn
) -> _TransactionFn:
    """Build the function that generates Transaction objects.

    Args:
        idl_ix: Instruction item from the IDL.
        ix_fn (_InstructionFn): The function that generates instructions.

    Returns:
        _TransactionFn: [description]
    """

    def tx_fn(*args: Any, ctx: Context = EMPTY_CONTEXT) -> Transaction:
        _check_args_length(idl_ix, args)
        tx = Transaction()
        if ctx.pre_instructions:
            tx.add(*ctx.pre_instructions)
        tx.add(ix_fn(*args, ctx=ctx))
        if ctx.post_instructions:
            tx.add(*ctx.post_instructions)
        return tx

    return tx_fn
