import hashlib
from typing import Any

from anchorpy.coder.idl import IdlCoder
from anchorpy.idl import Idl


class StateCoder(object):
    def __init__(self, idl: Idl):
        if not idl.state:
            raise Exception("Idl state not defined")
        self._layout = IdlCoder.typedef_layout(idl.state.struct, idl.types)

    def encode(self, name: str, account: Any) -> bytes:
        buf = bytes([0] * 1000)
        buf_len = self._layout.encode(account, buf)
        disc = state_discriminator(name)
        acc_data = buf[:buf_len]
        return disc + acc_data

    def decode(self, ix: bytes):
        data = ix[8:]
        return self._layout.decode(data)


def state_discriminator(name: str) -> bytes:
    return bytes(hashlib.sha256(f"state:{name}".encode("utf-8")).digest())[:8]
