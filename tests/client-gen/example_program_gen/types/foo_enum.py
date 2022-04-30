from . import bar_struct
from __future__ import annotations
import typing
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


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


class Unnamed(object):
    discriminator = 0
    kind = "Unnamed"

    def __init__(self, value: UnnamedFields) -> None:
        self.value = (value[0], value[1], bar_struct.BarStruct(**value[2]))

    def to_json(self) -> UnnamedJSON:
        return {
            "kind": "Unnamed",
            "value": [value[0], value[1], value[2].to_json()],
        }

    def to_encodable(self) -> dict:
        return {
            "Unnamed": {
                "_0": self.value[0],
                "_1": self.value[1],
                "_2": bar_struct.BarStruct.to_encodable(self.value[2]),
            },
        }


class UnnamedSingle(object):
    discriminator = 1
    kind = "UnnamedSingle"

    def __init__(self, value: UnnamedSingleFields) -> None:
        self.value = bar_struct.BarStruct(**value[0])

    def to_json(self) -> UnnamedSingleJSON:
        return {
            "kind": "UnnamedSingle",
            "value": [value[0].to_json()],
        }

    def to_encodable(self) -> dict:
        return {
            "UnnamedSingle": {
                "_0": bar_struct.BarStruct.to_encodable(self.value[0]),
            },
        }


class Named(object):
    discriminator = 2
    kind = "Named"

    def __init__(self, value: NamedFields) -> None:
        self.value = {
            "bool_field": value["bool_field"],
            "u8_field": value["u8_field"],
            "nested": bar_struct.BarStruct(**value["nested"]),
        }

    def to_json(self) -> NamedJSON:
        return {
            "kind": "Named",
            "value": {
                "bool_field": self.value["bool_field"],
                "u8_field": self.value["u8_field"],
                "nested": self.value["nested"].to_json(),
            },
        }

    def to_encodable(self) -> dict:
        return {
            "Named": {
                "bool_field": self.value["bool_field"],
                "u8_field": self.value["u8_field"],
                "nested": bar_struct.BarStruct.to_encodable(self.value["nested"]),
            },
        }


class Struct(object):
    discriminator = 3
    kind = "Struct"

    def __init__(self, value: StructFields) -> None:
        self.value = bar_struct.BarStruct(**value[0])

    def to_json(self) -> StructJSON:
        return {
            "kind": "Struct",
            "value": [value[0].to_json()],
        }

    def to_encodable(self) -> dict:
        return {
            "Struct": {
                "_0": bar_struct.BarStruct.to_encodable(self.value[0]),
            },
        }


class OptionStruct(object):
    discriminator = 4
    kind = "OptionStruct"

    def __init__(self, value: OptionStructFields) -> None:
        self.value = (value[0] and bar_struct.BarStruct(**value[0])) or None

    def to_json(self) -> OptionStructJSON:
        return {
            "kind": "OptionStruct",
            "value": [(value[0] and value[0].to_json()) or None],
        }

    def to_encodable(self) -> dict:
        return {
            "OptionStruct": {
                "_0": (
                    self.value[0] and bar_struct.BarStruct.to_encodable(self.value[0])
                )
                or None,
            },
        }


class VecStruct(object):
    discriminator = 5
    kind = "VecStruct"

    def __init__(self, value: VecStructFields) -> None:
        self.value = list(map(lambda item: bar_struct.BarStruct(**item), value[0]))

    def to_json(self) -> VecStructJSON:
        return {
            "kind": "VecStruct",
            "value": [list(map(lambda item: item.to_json(), value[0]))],
        }

    def to_encodable(self) -> dict:
        return {
            "VecStruct": {
                "_0": list(
                    map(
                        lambda item: bar_struct.BarStruct.to_encodable(item),
                        self.value[0],
                    )
                ),
            },
        }


class NoFields(object):
    discriminator = 6
    kind = "NoFields"

    @classmethod
    def to_json(cls) -> NoFieldsJSON:
        return {
            "kind": "NoFields",
        }

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
            (val["_0"], val["_1"], bar_struct.BarStruct.from_decoded(val["_2"]))
        )
    if "UnnamedSingle" in obj:
        val = obj["UnnamedSingle"]
        return UnnamedSingle((bar_struct.BarStruct.from_decoded(val["_0"])))
    if "Named" in obj:
        val = obj["Named"]
        return Named(
            {
                "bool_field": val["bool_field"],
                "u8_field": val["u8_field"],
                "nested": types.bar_struct.BarStruct.from_decoded(val["nested"]),
            }
        )
    if "Struct" in obj:
        val = obj["Struct"]
        return Struct((bar_struct.BarStruct.from_decoded(val["_0"])))
    if "OptionStruct" in obj:
        val = obj["OptionStruct"]
        return OptionStruct(
            ((val["_0"] and types.bar_struct.BarStruct.from_decoded(val["_0"])) or None)
        )
    if "VecStruct" in obj:
        val = obj["VecStruct"]
        return VecStruct(
            (list(map(lambda item: bar_struct.BarStruct.from_decoded(item), val["_0"])))
        )
    if "NoFields" in obj:
        return NoFields()
    raise ValueError("Invalid enum object")


def from_json(obj: FooEnumJSON) -> FooEnumKind:
    if obj["kind"] == "Unnamed":
        return Unnamed(
            (
                obj["value[0]"],
                obj["value[1]"],
                bar_struct.BarStruct.from_json(obj["value[2]"]),
            )
        )
    if obj["kind"] == "UnnamedSingle":
        return UnnamedSingle((bar_struct.BarStruct.from_json(obj["value[0]"])))
    if obj["kind"] == "Named":
        return Named(
            {
                "bool_field": obj["value"]["bool_field"],
                "u8_field": obj["value"]["u8_field"],
                "nested": bar_struct.BarStruct.from_json(obj["value"]["nested"]),
            }
        )
    if obj["kind"] == "Struct":
        return Struct((bar_struct.BarStruct.from_json(obj["value[0]"])))
    if obj["kind"] == "OptionStruct":
        return OptionStruct(
            (
                (obj["value[0]"] and bar_struct.BarStruct.from_json(obj["value[0]"]))
                or None
            )
        )
    if obj["kind"] == "VecStruct":
        return VecStruct(
            (
                list(
                    map(
                        lambda item: bar_struct.BarStruct.from_json(item),
                        obj["value[0]"],
                    )
                )
            )
        )
    if obj["kind"] == "NoFields":
        return NoFields()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Unnamed"
    / borsh.CStruct(
        "_0" / borsh.Bool, "_1" / borsh.U8, "_2" / bar_struct.BarStruct.layout
    ),
    "UnnamedSingle" / borsh.CStruct("_0" / bar_struct.BarStruct.layout),
    "Named"
    / borsh.CStruct(
        "bool_field" / borsh.Bool,
        "u8_field" / borsh.U8,
        "nested" / bar_struct.BarStruct.layout,
    ),
    "Struct" / borsh.CStruct("_0" / bar_struct.BarStruct.layout),
    "OptionStruct" / borsh.CStruct("_0" / borsh.Option(bar_struct.BarStruct.layout)),
    "VecStruct" / borsh.CStruct("_0" / borsh.Vec(bar_struct.BarStruct.layout)),
    "NoFields" / borsh.CStruct(),
)
