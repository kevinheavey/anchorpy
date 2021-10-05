from typing import Any, Callable, Dict

from solana.transaction import TransactionSignature

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
        # try:
        return provider.send(tx, ctx.signers, ctx.options)
        # except Exception as e:
        #     # translated_err = translate_err(idl_errors, tx_sig["error"])
        #     # TODO
        #     """
        #     let translatedErr = translateError(idlErrors, err);
        #     if (translatedErr === null) {
        #       throw err;
        #     }
        #     throw translatedErr;
        #     """
        #     print(f"Translating error: {e}", flush=True)

    return rpc_fn
