"""Extensions to the Borsh spec for Solana-specific types."""
from typing import Any, Dict, Type, TypeVar, cast
from keyword import kwlist
from dataclasses import asdict
from borsh_construct import CStruct, U8
from solana import publickey
from construct import (
    Bytes,
    Adapter,
    Container,
    Padding,
    Construct,
    IfThenElse,
    Switch,
    Renamed,
)


class BorshPubkeyAdapter(Adapter):
    def __init__(self) -> None:
        super().__init__(Bytes(32))  # type: ignore

    def _decode(self, obj: bytes, context, path) -> publickey.PublicKey:
        return publickey.PublicKey(obj)

    def _encode(self, obj: publickey.PublicKey, context, path) -> bytes:
        return bytes(obj)


class EnumForCodegen(Adapter):
    _index_key = "index"
    _value_key = "value"

    def __init__(self, *variants: "Renamed[CStruct, CStruct]") -> None:
        """Init enum."""  # noqa: DAR101
        switch_cases: dict[int, "Renamed[CStruct, CStruct]"] = {}
        variant_name_to_index: dict[str, int] = {}
        index_to_variant_name: dict[int, str] = {}
        for idx, parser in enumerate(variants):
            switch_cases[idx] = parser
            name = cast(str, parser.name)
            variant_name_to_index[name] = idx
            index_to_variant_name[idx] = name
        enum_struct = CStruct(
            self._index_key / U8,
            self._value_key
            / Switch(lambda this: this.index, cast(dict[int, Construct], switch_cases)),
        )
        super().__init__(enum_struct)  # type: ignore
        self.variant_name_to_index = variant_name_to_index
        self.index_to_variant_name = index_to_variant_name

    def _decode(self, obj: CStruct, context, path) -> dict[str, Any]:
        index = obj.index
        variant_name = self.index_to_variant_name[index]
        return {variant_name: obj.value}

    def _encode(self, obj: dict[str, Any], context, path) -> dict[str, Any]:
        variant_name = list(obj.keys())[0]
        index = self.variant_name_to_index[variant_name]
        return {self._index_key: index, self._value_key: obj[variant_name]}


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
        super().__init__(option_struct)  # type: ignore

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


BorshPubkey = BorshPubkeyAdapter()  # noqa: WPS462
"""Adapter for (de)serializing a public key."""  # noqa: WPS322
