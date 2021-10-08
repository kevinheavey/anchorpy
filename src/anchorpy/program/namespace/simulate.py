from typing import Dict, Any, List, NamedTuple

from solana.keypair import Keypair

from anchorpy.coder.coder import Coder
from anchorpy.idl import IdlInstruction, Idl
from anchorpy.program.event import EventParser, Event
from anchorpy.program.namespace.transaction import TransactionFn
from anchorpy.provider import Provider
from anchorpy.program.context import split_args_and_context
from solana.publickey import PublicKey


class SimulateResponse(NamedTuple):
    events: List[Event]
    raw: List[str]


def build_simulate_item(
    idl_ix: IdlInstruction,
    tx_fn: TransactionFn,
    idl_errors: Dict[int, str],
    provider: Provider,
    coder: Coder,
    program_id: PublicKey,
    idl: Idl,
):
    def simulate_fn(*args: Any) -> SimulateResponse:
        tx = tx_fn(*args)
        _, ctx = split_args_and_context(idl_ix, args)
        resp = provider.simulate(tx, ctx.signers, ctx.options)
        try:
            ok_res = resp["result"]
        except KeyError:
            err_res = resp["error"]
            translated_err = ""
            raise translated_err
        logs = ok_res["value"]["logs"]
        events = []
        if idl.events is not None:
            parser = EventParser(program_id, coder)
            parser.parse_logs(logs, lambda evt: events.append(evt))
        return SimulateResponse(events, logs)

    return simulate_fn
