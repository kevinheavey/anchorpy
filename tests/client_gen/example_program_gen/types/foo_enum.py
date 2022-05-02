from __future__ import annotations
from . import bar_struct
import typing
from dataclasses import dataclass
from construct import Construct
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh

UnnamedJSONValue = tuple[bool, int, bar_struct.BarStructJSON]
UnnamedSingleJSONValue = tuple[bar_struct.BarStructJSON]


class NamedJSONValue(typing.TypedDict):
    bool_field: bool
    u8_field: int
    nested: bar_struct.BarStructJSON


StructJSONValue = tuple[bar_struct.BarStructJSON]
OptionStructJSONValue = tuple[typing.Optional[bar_struct.BarStructJSON]]
VecStructJSONValue = tuple[list[bar_struct.BarStructJSON]]
UnnamedValue = tuple[bool, int, bar_struct.BarStruct]
UnnamedSingleValue = tuple[bar_struct.BarStruct]


class NamedValue(typing.TypedDict):
    bool_field: bool
    u8_field: int
    nested: bar_struct.BarStruct


StructValue = tuple[bar_struct.BarStruct]
OptionStructValue = tuple[typing.Optional[bar_struct.BarStruct]]
VecStructValue = tuple[list[bar_struct.BarStruct]]


class UnnamedJSON(typing.TypedDict):
    value: UnnamedJSONValue
    kind: typing.Literal["Unnamed"]


class UnnamedSingleJSON(typing.TypedDict):
    value: UnnamedSingleJSONValue
    kind: typing.Literal["UnnamedSingle"]


class NamedJSON(typing.TypedDict):
    value: NamedJSONValue
    kind: typing.Literal["Named"]


class StructJSON(typing.TypedDict):
    value: StructJSONValue
    kind: typing.Literal["Struct"]


class OptionStructJSON(typing.TypedDict):
    value: OptionStructJSONValue
    kind: typing.Literal["OptionStruct"]


class VecStructJSON(typing.TypedDict):
    value: VecStructJSONValue
    kind: typing.Literal["VecStruct"]


class NoFieldsJSON(typing.TypedDict):
    kind: typing.Literal["NoFields"]


@dataclass
class Unnamed:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Unnamed"
    value: UnnamedValue

    def to_json(self) -> UnnamedJSON:
        return UnnamedJSON(
            kind="Unnamed",
            value=(
                self.value[0],
                self.value[1],
                self.value[2].to_json(),
            ),
        )

    def to_encodable(self) -> dict:
        return {
            "Unnamed": {
                "item_0": self.value[0],
                "item_1": self.value[1],
                "item_2": self.value[2].to_encodable(),
            },
        }


@dataclass
class UnnamedSingle:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "UnnamedSingle"
    value: UnnamedSingleValue

    def to_json(self) -> UnnamedSingleJSON:
        return UnnamedSingleJSON(
            kind="UnnamedSingle",
            value=(self.value[0].to_json(),),
        )

    def to_encodable(self) -> dict:
        return {
            "UnnamedSingle": {
                "item_0": self.value[0].to_encodable(),
            },
        }


@dataclass
class Named:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "Named"
    value: NamedValue

    def to_json(self) -> NamedJSON:
        return NamedJSON(
            kind="Named",
            value={
                "bool_field": self.value["bool_field"],
                "u8_field": self.value["u8_field"],
                "nested": self.value["nested"].to_json(),
            },
        )

    def to_encodable(self) -> dict:
        return {
            "Named": {
                "bool_field": self.value["bool_field"],
                "u8_field": self.value["u8_field"],
                "nested": self.value["nested"].to_encodable(),
            },
        }


@dataclass
class Struct:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "Struct"
    value: StructValue

    def to_json(self) -> StructJSON:
        return StructJSON(
            kind="Struct",
            value=(self.value[0].to_json(),),
        )

    def to_encodable(self) -> dict:
        return {
            "Struct": {
                "item_0": self.value[0].to_encodable(),
            },
        }


@dataclass
class OptionStruct:
    discriminator: typing.ClassVar = 4
    kind: typing.ClassVar = "OptionStruct"
    value: OptionStructValue

    def to_json(self) -> OptionStructJSON:
        return OptionStructJSON(
            kind="OptionStruct",
            value=((None if self.value[0] is None else self.value[0].to_json()),),
        )

    def to_encodable(self) -> dict:
        return {
            "OptionStruct": {
                "item_0": (
                    None if self.value[0] is None else self.value[0].to_encodable()
                ),
            },
        }


@dataclass
class VecStruct:
    discriminator: typing.ClassVar = 5
    kind: typing.ClassVar = "VecStruct"
    value: VecStructValue

    def to_json(self) -> VecStructJSON:
        return VecStructJSON(
            kind="VecStruct",
            value=(list(map(lambda item: item.to_json(), self.value[0])),),
        )

    def to_encodable(self) -> dict:
        return {
            "VecStruct": {
                "item_0": list(map(lambda item: item.to_encodable(), self.value[0])),
            },
        }


@dataclass
class NoFields:
    discriminator: typing.ClassVar = 6
    kind: typing.ClassVar = "NoFields"

    @classmethod
    def to_json(cls) -> NoFieldsJSON:
        return NoFieldsJSON(
            kind="NoFields",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "NoFields": {},
        }


FooEnumKind = typing.Union[
    Unnamed, UnnamedSingle, Named, Struct, OptionStruct, VecStruct, NoFields
]
FooEnumJSON = typing.Union[
    UnnamedJSON,
    UnnamedSingleJSON,
    NamedJSON,
    StructJSON,
    OptionStructJSON,
    VecStructJSON,
    NoFieldsJSON,
]


def from_decoded(obj: dict) -> FooEnumKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Unnamed" in obj:
        val = obj["Unnamed"]
        return Unnamed(
            (
                val["item_0"],
                val["item_1"],
                bar_struct.BarStruct.from_decoded(val["item_2"]),
            )
        )
    if "UnnamedSingle" in obj:
        val = obj["UnnamedSingle"]
        return UnnamedSingle((bar_struct.BarStruct.from_decoded(val["item_0"]),))
    if "Named" in obj:
        val = obj["Named"]
        return Named(
            NamedValue(
                bool_field=val["bool_field"],
                u8_field=val["u8_field"],
                nested=bar_struct.BarStruct.from_decoded(val["nested"]),
            )
        )
    if "Struct" in obj:
        val = obj["Struct"]
        return Struct((bar_struct.BarStruct.from_decoded(val["item_0"]),))
    if "OptionStruct" in obj:
        val = obj["OptionStruct"]
        return OptionStruct(
            (
                (
                    None
                    if val["item_0"] is None
                    else bar_struct.BarStruct.from_decoded(val["item_0"])
                ),
            )
        )
    if "VecStruct" in obj:
        val = obj["VecStruct"]
        return VecStruct(
            (
                list(
                    map(
                        lambda item: bar_struct.BarStruct.from_decoded(item),
                        val["item_0"],
                    )
                ),
            )
        )
    if "NoFields" in obj:
        return NoFields()
    raise ValueError("Invalid enum object")


def from_json(obj: FooEnumJSON) -> FooEnumKind:
    if obj["kind"] == "Unnamed":
        unnamed_json_value = typing.cast(UnnamedJSONValue, obj["value"])
        return Unnamed(
            (
                unnamed_json_value[0],
                unnamed_json_value[1],
                bar_struct.BarStruct.from_json(unnamed_json_value[2]),
            )
        )
    if obj["kind"] == "UnnamedSingle":
        unnamed_single_json_value = typing.cast(UnnamedSingleJSONValue, obj["value"])
        return UnnamedSingle(
            (bar_struct.BarStruct.from_json(unnamed_single_json_value[0]),)
        )
    if obj["kind"] == "Named":
        named_json_value = typing.cast(NamedJSONValue, obj["value"])
        return Named(
            NamedValue(
                bool_field=named_json_value["bool_field"],
                u8_field=named_json_value["u8_field"],
                nested=bar_struct.BarStruct.from_json(named_json_value["nested"]),
            )
        )
    if obj["kind"] == "Struct":
        struct_json_value = typing.cast(StructJSONValue, obj["value"])
        return Struct((bar_struct.BarStruct.from_json(struct_json_value[0]),))
    if obj["kind"] == "OptionStruct":
        option_struct_json_value = typing.cast(OptionStructJSONValue, obj["value"])
        return OptionStruct(
            (
                (
                    None
                    if option_struct_json_value[0] is None
                    else bar_struct.BarStruct.from_json(option_struct_json_value[0])
                ),
            )
        )
    if obj["kind"] == "VecStruct":
        vec_struct_json_value = typing.cast(VecStructJSONValue, obj["value"])
        return VecStruct(
            (
                list(
                    map(
                        lambda item: bar_struct.BarStruct.from_json(item),
                        vec_struct_json_value[0],
                    )
                ),
            )
        )
    if obj["kind"] == "NoFields":
        return NoFields()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Unnamed"
    / borsh.CStruct(
        "item_0" / borsh.Bool,
        "item_1" / borsh.U8,
        "item_2" / bar_struct.BarStruct.layout,
    ),
    "UnnamedSingle" / borsh.CStruct("item_0" / bar_struct.BarStruct.layout),
    "Named"
    / borsh.CStruct(
        "bool_field" / borsh.Bool,
        "u8_field" / borsh.U8,
        "nested" / bar_struct.BarStruct.layout,
    ),
    "Struct" / borsh.CStruct("item_0" / bar_struct.BarStruct.layout),
    "OptionStruct"
    / borsh.CStruct("item_0" / borsh.Option(bar_struct.BarStruct.layout)),
    "VecStruct"
    / borsh.CStruct(
        "item_0" / borsh.Vec(typing.cast(Construct, bar_struct.BarStruct.layout))
    ),
    "NoFields" / borsh.CStruct(),
)
