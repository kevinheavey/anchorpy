"""This module contains code for creating simulate functions."""
from typing import Dict, Any, NamedTuple, Protocol, Awaitable

from solders.rpc.responses import SimulateTransactionResp


from anchorpy.coder.coder import Coder
from anchorpy.error import ProgramError
from anchorpy.idl import _IdlInstruction, Idl
from anchorpy.program.event import EventParser, Event
from anchorpy.program.namespace.transaction import _TransactionFn
from anchorpy.provider import Provider
from anchorpy.program.context import EMPTY_CONTEXT, Context, _check_args_length
from solana.publickey import PublicKey
from solana.rpc.core import RPCException


class SimulateResponse(NamedTuple):
    """The result of a simulate function call."""

    events: list[Event]
    raw: list[str]


class _SimulateFn(Protocol):
    """A single method generated from an IDL.

    It simulates a method against a cluster configured by the provider,
    returning a list of all the events and raw logs that were emitted
    during the execution of the method.
    """

    def __call__(
        self,
        *args: Any,
        ctx: Context = EMPTY_CONTEXT,
    ) -> Awaitable[SimulateResponse]:
        """Protocol definition.

        Args:
            *args: The positional arguments for the program. The type and number
                of these arguments depend on the program being used.
            ctx: non-argument parameters to pass to the method.

        """


def _build_simulate_item(
    idl_ix: _IdlInstruction,
    tx_fn: _TransactionFn,
    idl_errors: Dict[int, str],
    provider: Provider,
    coder: Coder,
    program_id: PublicKey,
    idl: Idl,
) -> _SimulateFn:
    """Build the function to simulate transactions for a given method of a program.

    Args:
        idl_ix: An IDL instruction object.
        tx_fn: The function to generate the `Transaction` object.
        idl_errors: Mapping of error code to message.
        provider: A provider instance.
        coder: The program's coder object.
        program_id: The program ID.
        idl: The parsed Idl instance.

    Returns:
        The simulate function.
    """

    async def simulate_fn(*args: Any, ctx: Context = EMPTY_CONTEXT) -> SimulateResponse:
        tx = tx_fn(*args, ctx=ctx)
        _check_args_length(idl_ix, args)
        resp = await provider.simulate(tx, ctx.signers, ctx.options)
        if isinstance(resp, SimulateTransactionResp):
            ok_res = resp.value
        else:
            err_res = resp.error
            translated_err = ProgramError.parse(err_res, idl_errors)
            if translated_err is not None:
                raise translated_err
            raise RPCException(err_res)
        logs = ok_res.logs or []
        events = []
        if idl.events is not None:
            parser = EventParser(program_id, coder)
            parser.parse_logs(logs, lambda evt: events.append(evt))
        return SimulateResponse(events, logs)

    return simulate_fn
