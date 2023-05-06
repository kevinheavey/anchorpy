"""This module contains code for creating simulate functions."""
from typing import Any, Awaitable, Dict, NamedTuple, Protocol

from anchorpy_core.idl import Idl, IdlInstruction
from solana.rpc.commitment import Confirmed
from solana.rpc.core import RPCException
from solders.pubkey import Pubkey

from anchorpy.coder.coder import Coder
from anchorpy.error import ProgramError
from anchorpy.program.context import EMPTY_CONTEXT, Context, _check_args_length
from anchorpy.program.event import Event, EventParser
from anchorpy.program.namespace.transaction import _TransactionFn
from anchorpy.provider import Provider


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
    idl_ix: IdlInstruction,
    tx_fn: _TransactionFn,
    idl_errors: Dict[int, str],
    provider: Provider,
    coder: Coder,
    program_id: Pubkey,
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
        blockhash = (
            await provider.connection.get_latest_blockhash(Confirmed)
        ).value.blockhash
        tx = tx_fn(*args, payer=provider.wallet.payer, blockhash=blockhash, ctx=ctx)
        _check_args_length(idl_ix, args)
        resp = (await provider.simulate(tx, ctx.options)).value
        resp_err = resp.err
        logs = resp.logs or []
        if resp_err is None:
            events = []
            if idl.events is not None:
                parser = EventParser(program_id, coder)
                parser.parse_logs(logs, lambda evt: events.append(evt))
            return SimulateResponse(events, logs)
        else:
            translated_err = ProgramError.parse_tx_error(
                resp_err, idl_errors, program_id, logs
            )
            if translated_err is not None:
                raise translated_err
            raise RPCException(resp_err)

    return simulate_fn
