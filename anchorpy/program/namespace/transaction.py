from typing import Any, Callable, List

from solana.transaction import Transaction

from anchorpy.program.context import split_args_and_context
from anchorpy.idl import IdlInstruction
from anchorpy.program.namespace.instruction import InstructionFn


TransactionFn = Callable[[Any], Transaction]


class TransactionNamespace(object):
    pass


# ts TransactionNamespaceFactory.build
def build_transaction_fn(idl_ix: IdlInstruction, ix_fn: InstructionFn) -> TransactionFn:
    def tx_fn(*args: List[Any]) -> Transaction:
        _, ctx = split_args_and_context(idl_ix, args)
        tx = Transaction()
        if ctx.instructions:
            tx.add(*ctx.instructions)
        tx.add(ix_fn(*args))
        return tx

    return tx_fn
