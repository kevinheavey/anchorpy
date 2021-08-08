import hashlib
from typing import Dict, Any

from shitty_borsh.borsh import Layout
from anchorpy.coder.idl import IdlCoder
from anchorpy.idl import Idl

ACCOUNT_DISCRIMINATOR_SIZE = 8  # bytes


class AccountsCoder(object):
    def __init__(self, idl: Idl):
        self._accounts_layout: Dict[str, Layout] = dict()
        for acc in idl.accounts:
            self._accounts_layout[acc.name] = IdlCoder.typedef_layout(acc, idl.types)

    def encode(self, account_name: str, account: Any) -> bytes:
        buffer = bytes([0] * 1000)
        layout = self._accounts_layout[account_name]
        layout_len = layout.encode(account, buffer)
        account_data = buffer[:layout_len]
        discriminator = account_discriminator(account_name)
        return discriminator + account_data

    def decode(self, account_name: str, ix: bytes) -> Any:
        data = ix[8:]
        return self._accounts_layout[account_name].decode(data)[1]


def account_discriminator(name: str) -> bytes:
    """
    // Calculates unique 8 byte discriminator prepended to all anchor accounts.
    export async function accountDiscriminator(name: string): Promise<Buffer> {
      return Buffer.from(sha256.digest(`account:${name}`)).slice(0, 8);
    }
    """
    return bytes(hashlib.sha256(f"account:{name}".encode("utf-8")).digest())[:8]
