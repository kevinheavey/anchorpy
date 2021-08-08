from typing import Dict

from anchorpy.coder.coder import Coder
from anchorpy.idl import IdlInstruction, Idl
from anchorpy.program.namespace.transaction import TransactionFn
from anchorpy.provider import Provider
from anchorpy.public_key import PublicKey


class SimulateFactory(object):
    @staticmethod
    def build(idl_ix: IdlInstruction,
              tx_fn: TransactionFn,
              idl_errors: Dict[int, str],
              provider: Provider,
              coder: Coder,
              program_id: PublicKey,
              idl: Idl):
        pass


class SimulateNamespace(object):
    pass
