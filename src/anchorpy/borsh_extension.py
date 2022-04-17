"""Extensions to the Borsh spec for Solana-specific types."""
from typing import Any, Dict, Type, TypeVar
from keyword import kwlist
from dataclasses import asdict
from borsh_construct import CStruct
from solana import publickey
from construct import Bytes, Adapter, Container, Padding, Construct


class _BorshPubkeyAdapter(Adapter):
    def __init__(self) -> None:
        super().__init__(Bytes(32))  # type: ignore

    def _decode(self, obj: bytes, context, path) -> publickey.PublicKey:
        return publickey.PublicKey(obj)

    def _encode(self, obj: publickey.PublicKey, context, path) -> bytes:
        return bytes(obj)


class COption(Adapter):
    _discriminator_key = "discriminator"
    _value_key = "value"

    def __init__(self, subcon: Construct) -> None:
        option_struct = CStruct(
            self._discriminator_key / U8,
            self._value_key
            / IfThenElse(
                lambda this: this[self._discriminator_key] == 0,
                Padding(subcon.sizeof()),
                subcon,
            ),
        )

    def _decode(self, obj, context, path) -> Any:
        discriminator = obj[self._discriminator_key]
        return None if discriminator == 0 else obj[self._value_key]

    def _encode(self, obj, context, path) -> dict:
        discriminator = 0 if obj is None else 1
        return {self._discriminator_key: discriminator, self._value_key: obj}


T = TypeVar("T")


class _DataclassStruct(Adapter):
    """Converts dataclasses to/from `borsh_construct.CStruct`."""

    def __init__(self, cstruct: CStruct, datacls: Type[T]) -> None:
        """Init.

        Args:
            cstruct: The underlying `CStruct`.
            datacls: The dataclass type.
        """
        super().__init__(cstruct)  # type: ignore
        self.datacls = datacls

    def _decode(self, obj: Container, context, path) -> T:
        kwargs = {}
        for key, value in obj.items():
            if key[0] != "_":
                key_to_use = f"{key}_" if key in kwlist else key
                kwargs[key_to_use] = value
        return self.datacls(**kwargs)  # type: ignore

    def _encode(self, obj: T, context, path) -> Dict[str, Any]:
        if isinstance(obj, dict):
            return obj
        return asdict(obj)


_BorshPubkey = _BorshPubkeyAdapter()  # noqa: WPS462
"""Adapter for (de)serializing a public key."""  # noqa: WPS322
