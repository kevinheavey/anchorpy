"""This module deals with generating transactions."""
from typing import Any, Protocol

from solana.transaction import Transaction

from anchorpy.program.context import EMPTY_CONTEXT, Context, check_args_length
from anchorpy.idl import _IdlInstruction  # noqa: WPS450
from anchorpy.program.namespace.instruction import InstructionFn


class TransactionFn(Protocol):
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
def build_transaction_fn(
    idl_ix: _IdlInstruction, ix_fn: InstructionFn
) -> TransactionFn:
    """Build the function that generates Transaction objects.

    Args:
        idl_ix: Instruction item from the IDL.
        ix_fn (InstructionFn): The function that generates instructions.

    Returns:
        TransactionFn: [description]
    """

    def tx_fn(*args: Any, ctx: Context = EMPTY_CONTEXT) -> Transaction:
        check_args_length(idl_ix, args)
        tx = Transaction()
        if ctx.instructions:
            tx.add(*ctx.instructions)
        tx.add(ix_fn(*args, ctx=ctx))
        return tx

    return tx_fn
