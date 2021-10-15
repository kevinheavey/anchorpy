from typing import Dict, Any, List, NamedTuple, Union, cast, Protocol

from solana.rpc.types import RPCError


from anchorpy.coder.coder import Coder
from anchorpy.error import ExtendedRPCError, ProgramError
from anchorpy.idl import IdlInstruction, Idl
from anchorpy.program.event import EventParser, Event
from anchorpy.program.namespace.transaction import TransactionFn
from anchorpy.provider import Provider
from anchorpy.program.context import EMPTY_CONTEXT, Context, check_args_length
from solana.publickey import PublicKey
from solana.rpc.core import RPCException


class SimulateResponse(NamedTuple):
    events: List[Event]
    raw: List[str]


class SimulateFn(Protocol):
    """A single method generated from an IDL.

    It simulates a method against a cluster configured by the provider,
    returning a list of all the events and raw logs that were emitted
    during the execution of the method.
    """

    def __call__(self, *args: Any, ctx: Context = EMPTY_CONTEXT) -> SimulateResponse:
        """Protocol definition.

        Args:
            *args: The positional arguments for the program. The type and number
                of these arguments depend on the program being used.
            ctx: non-argument parameters to pass to the method.

        """


def build_simulate_item(
    idl_ix: IdlInstruction,
    tx_fn: TransactionFn,
    idl_errors: Dict[int, str],
    provider: Provider,
    coder: Coder,
    program_id: PublicKey,
    idl: Idl,
) -> SimulateFn:
    def simulate_fn(*args: Any, ctx: Context = EMPTY_CONTEXT) -> SimulateResponse:
        tx = tx_fn(*args, ctx=ctx)
        check_args_length(idl_ix, args)
        resp = provider.simulate(tx, ctx.signers, ctx.options)
        try:
            ok_res = resp["result"]
        except KeyError:
            err_res = cast(Union[ExtendedRPCError, RPCError], resp["error"])
            translated_err = ProgramError.parse(err_res, idl_errors)
            if translated_err is not None:
                raise translated_err
            raise RPCException(err_res)
        logs = ok_res["value"]["logs"]
        events = []
        if idl.events is not None:
            parser = EventParser(program_id, coder)
            parser.parse_logs(logs, lambda evt: events.append(evt))
        return SimulateResponse(events, logs)

    return simulate_fn
