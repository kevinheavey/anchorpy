from typing import Any, Tuple, Optional
import inflection

from anchorpy.program.namespace.rpc import (
    RpcNamespace,
    build_rpc_item,
)
from anchorpy.program.namespace.transaction import (
    TransactionNamespace,
    build_transaction_fn,
)
from anchorpy.coder.coder import Coder
from anchorpy.program.namespace.account import build_account
from anchorpy.program.namespace.simulate import SimulateFactory, SimulateNamespace
from anchorpy.program.namespace.instruction import (
    build_instruction_fn,
    InstructionNamespace,
)
from anchorpy.program.common import parse_idl_errors
from anchorpy.idl import Idl
from anchorpy.provider import Provider
from solana.publickey import PublicKey


def build_namespace(  # ts: NamespaceFactory.build
    idl: Idl, coder: Coder, program_id: PublicKey, provider: Provider
) -> Tuple[
    RpcNamespace,
    InstructionNamespace,
    TransactionNamespace,
    object,
    SimulateNamespace,
]:
    idl_errors = parse_idl_errors(idl)

    rpc = RpcNamespace()
    instruction = InstructionNamespace()
    transaction = TransactionNamespace()
    simulate = SimulateNamespace()

    for idl_ix in idl.instructions:

        def encode_fn(ix_name: str, ix: Any) -> bytes:
            return coder.instruction.encode(ix_name, ix)

        ix_item = build_instruction_fn(idl_ix, encode_fn, program_id)
        tx_item = build_transaction_fn(idl_ix, ix_item)
        rpc_item = build_rpc_item(idl_ix, tx_item, idl_errors, provider)
        simulate_item = SimulateFactory.build(
            idl_ix, tx_item, idl_errors, provider, coder, program_id, idl
        )

        name = inflection.camelize(idl_ix.name, False)
        setattr(instruction, name, ix_item)
        setattr(transaction, name, tx_item)
        setattr(rpc, name, rpc_item)
        setattr(simulate, name, simulate_item)

    account = build_account(idl, coder, program_id, provider) if idl.accounts else {}
    return rpc, instruction, transaction, account, simulate
