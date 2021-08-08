from typing import Any
import inflection

from anchorpy.program.namespace.rpc import RpcNamespace, RpcNamespaceFactory
from anchorpy.program.namespace.transaction import TransactionNamespace, TransactionNamespaceFactory
from anchorpy.coder.coder import Coder
from anchorpy.program.namespace.account import AccountFactory
from anchorpy.program.namespace.simulate import SimulateFactory, SimulateNamespace
from anchorpy.program.namespace.instruction import InstructionNamespaceFactory, InstructionNamespace
from anchorpy.program.namespace.state import StateFactory
from anchorpy.program.common import parse_idl_errors
from anchorpy.idl import Idl
from anchorpy.provider import Provider
from anchorpy.public_key import PublicKey


class NamespaceFactory(object):
    @staticmethod
    def build(idl: Idl, coder: Coder, program_id: PublicKey, provider: Provider):
        idl_errors = parse_idl_errors(idl)

        rpc = RpcNamespace()
        instruction = InstructionNamespace()
        transaction = TransactionNamespace()
        simulate = SimulateNamespace()

        state = StateFactory.build(
            idl,
            coder,
            program_id,
            provider
        )

        for idl_ix in idl.instructions:
            def encode_fn(ix_name: str, ix: Any) -> bytes:
                return coder.instruction.encode(ix_name, ix)

            ix_item = InstructionNamespaceFactory.build(idl_ix, encode_fn, program_id)
            tx_item = TransactionNamespaceFactory.build(idl_ix, ix_item)
            rpc_item = RpcNamespaceFactory.build(idl_ix, tx_item, idl_errors, provider)
            simulate_item = SimulateFactory.build(idl_ix, tx_item, idl_errors, provider, coder, program_id, idl)

            name = inflection.camelize(idl_ix.name, False)
            setattr(instruction, name, ix_item)
            setattr(transaction, name, tx_item)
            setattr(rpc, name, rpc_item)
            setattr(simulate, name, simulate_item)

        account = AccountFactory.build(idl, coder, program_id, provider) if idl.accounts else {}
        return rpc, instruction, transaction, account, simulate, state
