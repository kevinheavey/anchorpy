from typing import Dict, Any

import inflection

from shitty_borsh.borsh import Layout, Struct
from anchorpy.coder.common import sighash
from anchorpy.coder.idl import IdlCoder
from anchorpy.idl import Idl

SIGHASH_STATE_NAMESPACE = "state"
SIGHASH_GLOBAL_NAMESPACE = "global"


class InstructionCoder(object):
    def __init__(self, idl: Idl):
        self._ix_layout: Dict[str, Layout] = InstructionCoder.parse_ix_layout(idl)

    def encode(self, ix_name: str, ix: Any) -> bytes:
        return self._encode(SIGHASH_GLOBAL_NAMESPACE, ix_name, ix)

    def encode_state(self, ix_name: str, ix: Any) -> bytes:
        return self._encode(SIGHASH_STATE_NAMESPACE, ix_name, ix)

    def _encode(self, namespace: str, ix_name: str, ix: Any) -> bytes:
        method_name = inflection.camelize(ix_name, False)
        data = self._ix_layout[method_name].encode(ix)
        return sighash(namespace, ix_name) + data

    @staticmethod
    def parse_ix_layout(idl: Idl) -> Dict[str, Layout]:
        ix_layout: Dict[str, Layout] = dict()
        ixs = idl.state.methods + idl.instructions if idl.state else idl.instructions
        for ix in ixs:
            field_layouts = [IdlCoder.field_layout(arg, idl.types) for arg in ix.args]
            name = inflection.camelize(ix.name, False)
            ix_layout[name] = Struct(field_layouts, name)
        return ix_layout
