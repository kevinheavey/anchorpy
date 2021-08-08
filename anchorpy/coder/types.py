from typing import Dict, Any

from shitty_borsh.borsh import Layout
from anchorpy.coder.idl import IdlCoder
from anchorpy.idl import Idl


class TypesCoder(object):
    def __init__(self, idl: Idl):
        self._layouts: Dict[str, Layout] = dict()

        for acc in idl.types:
            self._layouts[acc.name] = IdlCoder.typedef_layout(acc, idl.types)

    def encode(self, account_name: str, account: Any) -> bytes:
        buf = bytes([0] * 1000)
        layout = self._layouts[account_name]
        buf_len = layout.encode(account, buf)
        return buf[:buf_len]

    def decode(self, account_name: str, ix: bytes) -> Any:
        return self._layouts[account_name].decode(ix)[1]
