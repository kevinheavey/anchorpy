from typing import Any, Awaitable, Dict, Protocol
from solana.rpc.core import RPCException

from solana.transaction import TransactionSignature
from anchorpy.error import ProgramError

from anchorpy.program.context import EMPTY_CONTEXT, Context, check_args_length
from anchorpy.idl import IdlInstruction
from anchorpy.provider import Provider
from anchorpy.program.namespace.transaction import TransactionFn


class RpcFn(Protocol):
    """RpcFn is a single RPC method generated from an IDL, sending a transaction paid for and signed by the configured provider."""  # noqa: E501

    def __call__(
        self,
        *args: Any,
        ctx: Context = EMPTY_CONTEXT,
    ) -> Awaitable[TransactionSignature]:
        """
        Args:
            *args: The positional arguments for the program. The type and number
                of these arguments depend on the program being used.
            ctx: non-argument parameters to pass to the method.
        """
        ...


def build_rpc_item(  # ts: RpcFactory
    idl_ix: IdlInstruction,
    tx_fn: TransactionFn,
    idl_errors: Dict[int, str],
    provider: Provider,
) -> RpcFn:
    async def rpc_fn(*args: Any, ctx: Context = EMPTY_CONTEXT) -> TransactionSignature:
        tx = tx_fn(*args, ctx=ctx)
        check_args_length(idl_ix, args)
        try:
            return await provider.send(tx, ctx.signers, ctx.options)
        except RPCException as e:
            err_info = e.args[0]
            translated_err = ProgramError.parse(err_info, idl_errors)
            if translated_err is not None:
                raise translated_err from e
            raise

    return rpc_fn
