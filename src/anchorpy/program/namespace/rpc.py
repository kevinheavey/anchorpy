from typing import Any, Callable, Dict
from solana.rpc.core import RPCException

from solana.transaction import TransactionSignature
from anchorpy.error import ProgramError

from anchorpy.program.context import split_args_and_context
from anchorpy.idl import IdlInstruction
from anchorpy.provider import Provider
from anchorpy.program.namespace.transaction import TransactionFn


RpcFn = Callable[[Any], TransactionSignature]


def build_rpc_item(  # ts: RpcFactory
    idl_ix: IdlInstruction,
    tx_fn: TransactionFn,
    idl_errors: Dict[int, str],
    provider: Provider,
) -> RpcFn:
    def rpc_fn(*args: Any) -> TransactionSignature:
        tx = tx_fn(*args)
        _, ctx = split_args_and_context(idl_ix, args)
        try:
            return provider.send(tx, ctx.signers, ctx.options)
        except RPCException as e:
            err_info = e.args[0]
            translated_err = ProgramError.parse(err_info, idl_errors)
            if translated_err is not None:
                raise translated_err from e
            raise

    return rpc_fn
