from typing import Any, Protocol

from solana.transaction import Transaction

from anchorpy.program.context import EMPTY_CONTEXT, Context, check_args_length
from anchorpy.idl import IdlInstruction
from anchorpy.program.namespace.instruction import InstructionFn


class TransactionFn(Protocol):
    """A function to create a `Transaction` for a given program instruction."""

    def __call__(self, *args: Any, ctx: Context = EMPTY_CONTEXT) -> Transaction:
        """
        Args:
            *args: The positional arguments for the program. The type and number
                of these arguments depend on the program being used.
            ctx: non-argument parameters to pass to the method.
        """
        ...


class TransactionNamespace(object):
    pass


# ts TransactionNamespaceFactory.build
def build_transaction_fn(idl_ix: IdlInstruction, ix_fn: InstructionFn) -> TransactionFn:
    def tx_fn(*args: Any, ctx: Context = EMPTY_CONTEXT) -> Transaction:
        check_args_length(idl_ix, args)
        tx = Transaction()
        if ctx.instructions:
            tx.add(*ctx.instructions)
        tx.add(ix_fn(*args, ctx=ctx))
        return tx

    return tx_fn
