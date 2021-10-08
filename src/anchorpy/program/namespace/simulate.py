from typing import Dict, Any, List, NamedTuple

from anchorpy.coder.coder import Coder
from anchorpy.idl import IdlInstruction, Idl
from anchorpy.program.namespace.transaction import TransactionFn
from anchorpy.provider import Provider
from anchorpy.program.context import split_args_and_context
from solana.publickey import PublicKey


class Event(NamedTuple):
    name: str
    data: dict


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
        logs = resp["value"]["logs"]
        events = []
        print(logs)
