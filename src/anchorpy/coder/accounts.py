"""This module provides `AccountsCoder` and `_account_discriminator`."""
from hashlib import sha256
from typing import Tuple, Any
from construct import Adapter, Sequence, Bytes, Switch, Container

from anchorpy.coder.idl import _typedef_layout
from anchorpy.idl import Idl
from anchorpy.program.common import Instruction as AccountToSerialize

ACCOUNT_DISCRIMINATOR_SIZE = 8  # bytes


class AccountsCoder(Adapter):
    """Encodes and decodes account data."""

    def __init__(self, idl: Idl) -> None:
        """Init.

        Args:
            idl: The parsed IDL object.
        """
        self._accounts_layout = {
            acc.name: _typedef_layout(acc, idl.types, acc.name) for acc in idl.accounts
        }
        self.acc_name_to_discriminator = {
            acc.name: _account_discriminator(acc.name) for acc in idl.accounts
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

    def decode(self, obj: bytes) -> Container[Any]:
        """Decode account data.

        Args:
            obj: Data to decode.

        Returns:
            Decoded data.
        """
        return self.parse(obj).data

    def _decode(self, obj: Tuple[bytes, Any], context, path) -> AccountToSerialize:
        return AccountToSerialize(
            data=obj[1],
            name=self.discriminator_to_acc_name[obj[0]],
        )

    def _encode(self, obj: AccountToSerialize, context, path) -> Tuple[bytes, Any]:
        discriminator = self.acc_name_to_discriminator[obj.name]
        return discriminator, obj.data


def _account_discriminator(name: str) -> bytes:
    """Calculate unique 8 byte discriminator prepended to all anchor accounts.

    Args:
        name: The account name.

    Returns:
        The discriminator in bytes.
    """
    return sha256(f"account:{name}".encode()).digest()[:ACCOUNT_DISCRIMINATOR_SIZE]
