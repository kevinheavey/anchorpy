from typing import Dict, Any

from construct import Construct
from anchorpy.coder.idl import typedef_layout
from anchorpy.idl import Idl


class TypesCoder(object):
    def __init__(self, idl: Idl):
        self._layouts: Dict[str, Construct] = {
            acc.name: typedef_layout(acc, idl.types, acc.name) for acc in idl.types
        }

    def encode(self, account_name: str, account: Any) -> bytes:
        buf = bytes([0] * 1000)
        layout = self._layouts[account_name]
        buf_len = layout.encode(account, buf)
        return buf[:buf_len]

    def decode(self, account_name: str, ix: bytes) -> Any:
        return self._layouts[account_name].decode(ix)[1]
