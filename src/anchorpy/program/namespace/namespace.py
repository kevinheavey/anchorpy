from typing import Tuple

from anchorpy.program.namespace.rpc import (
    build_rpc_item,
)
from anchorpy.program.namespace.transaction import (
    build_transaction_fn,
)
from anchorpy.coder.coder import Coder
from anchorpy.program.namespace.account import build_account
from anchorpy.program.namespace.simulate import (
    build_simulate_item,
)
from anchorpy.program.namespace.instruction import (
    build_instruction_fn,
)
from anchorpy.program.common import parse_idl_errors
from anchorpy.idl import Idl
from anchorpy.provider import Provider
from solana.publickey import PublicKey


def build_namespace(  # ts: NamespaceFactory.build
    idl: Idl, coder: Coder, program_id: PublicKey, provider: Provider
) -> Tuple[dict, dict, dict, dict, dict]:
    idl_errors = parse_idl_errors(idl)

    rpc = {}
    instruction = {}
    transaction = {}
    simulate = {}

    for idl_ix in idl.instructions:

        ix_item = build_instruction_fn(idl_ix, coder.instruction.build, program_id)
        tx_item = build_transaction_fn(idl_ix, ix_item)
        rpc_item = build_rpc_item(idl_ix, tx_item, idl_errors, provider)
        simulate_item = build_simulate_item(
            idl_ix,
            tx_item,
            idl_errors,
            provider,
            coder,
            program_id,
            idl,
        )

        name = idl_ix.name
        instruction[name] = ix_item
        transaction[name] = tx_item
        rpc[name] = rpc_item
        simulate[name] = simulate_item

    account = build_account(idl, coder, program_id, provider) if idl.accounts else {}
    return rpc, instruction, transaction, account, simulate
