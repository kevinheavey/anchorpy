import hashlib
from typing import Dict, Any
from construct import Construct

from anchorpy.coder.idl import typedef_layout
from anchorpy.idl import Idl

ACCOUNT_DISCRIMINATOR_SIZE = 8  # bytes


class AccountsCoder(object):
    def __init__(self, idl: Idl):
        self._accounts_layout: Dict[str, Construct] = {}
        for acc in idl.accounts:
            self._accounts_layout[acc.name] = typedef_layout(acc, idl.types)

    def encode(self, account_name: str, account: Any) -> bytes:
        layout = self._accounts_layout[account_name]
        account_data = layout.build(account)
        discriminator = account_discriminator(account_name)
        return discriminator + account_data

    def decode(self, account_name: str, ix: bytes) -> Any:
        data = ix[8:]
        return self._accounts_layout[account_name].parse(data)[1]


def account_discriminator(name: str) -> bytes:
    """
    // Calculates unique 8 byte discriminator prepended to all anchor accounts.
    export async function accountDiscriminator(name: string): Promise<Buffer> {
      return Buffer.from(sha256.digest(`account:${name}`)).slice(0, 8);
    }
    """
    return bytes(hashlib.sha256(f"account:{name}".encode("utf-8")).digest())[:8]


if __name__ == "__main__":
    from json import loads
    from pathlib import Path

    data = loads((Path.home() / "anchorpy/idls/basic_1.json").read_text())
    idl = Idl.from_json(data)
    idl_accs = idl.accounts
    breakpoint()
