from hashlib import sha256
from typing import Tuple, Any
from construct import Adapter, Sequence, Bytes, Switch

from anchorpy.coder.idl import typedef_layout
from anchorpy.idl import Idl
from anchorpy.program.common import Instruction as AccountToSerialize

ACCOUNT_DISCRIMINATOR_SIZE = 8  # bytes


class AccountsCoder(Adapter):
    """Encodes and decodes account data."""

    def __init__(self, idl: Idl) -> None:
        self._accounts_layout = {
            acc.name: typedef_layout(acc, idl.types) for acc in idl.accounts
        }
        self.acc_name_to_discriminator = {
            acc.name: account_discriminator(acc.name) for acc in idl.accounts
        }
        self.discriminator_to_acc_name = {
            disc: acc_name for acc_name, disc in self.acc_name_to_discriminator.items()
        }
        discriminator_to_typedef_layout = {
            disc: self._accounts_layout[acc_name]
            for acc_name, disc in self.acc_name_to_discriminator.items()
        }
        subcon = Sequence(
            "discriminator" / Bytes(ACCOUNT_DISCRIMINATOR_SIZE),
            Switch(lambda this: this.discriminator, discriminator_to_typedef_layout),
        )
        super().__init__(subcon)  # type: ignore

    def _decode(self, obj: Tuple[bytes, Any], context, path) -> AccountToSerialize:
        return {"data": obj[1], "name": self.discriminator_to_acc_name[obj[0]]}

    def _encode(self, obj: AccountToSerialize, context, path) -> Tuple[bytes, Any]:
        discriminator = self.acc_name_to_discriminator[obj["name"]]
        return discriminator, obj["data"]


def account_discriminator(name: str) -> bytes:
    """Calculate unique 8 byte discriminator prepended to all anchor accounts."""
    return sha256(f"account:{name}".encode()).digest()[:ACCOUNT_DISCRIMINATOR_SIZE]
