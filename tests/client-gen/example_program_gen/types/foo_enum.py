from __future__ import annotations
from . import bar_struct
import typing
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
UnnamedFields = tuple[bool, int, bar_struct.BarStructFields]
UnnamedSingleFields = tuple[bar_struct.BarStructFields]


class NamedFields(typing.TypedDict):
    bool_field: bool
    u8_field: int
    nested: bar_struct.BarStructFields


StructFields = tuple[bar_struct.BarStructFields]
OptionStructFields = tuple[typing.Optional[bar_struct.BarStructFields]]
VecStructFields = tuple[list[bar_struct.BarStructFields]]
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


class Unnamed:
    discriminator = 0
    kind = "Unnamed"

    def __init__(self, value: UnnamedFields) -> None:
        self.value: UnnamedValue = (
            value[0],
            value[1],
            bar_struct.BarStruct(**value[2]),
        )

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
                "_0": self.value[0],
                "_1": self.value[1],
                "_2": bar_struct.BarStruct.to_encodable(self.value[2]),
            },
        }


class UnnamedSingle:
    discriminator = 1
    kind = "UnnamedSingle"

    def __init__(self, value: UnnamedSingleFields) -> None:
        self.value: UnnamedSingleValue = (bar_struct.BarStruct(**value[0]),)

    def to_json(self) -> UnnamedSingleJSON:
        return UnnamedSingleJSON(
            kind="UnnamedSingle",
            value=(self.value[0].to_json(),),
        )

    def to_encodable(self) -> dict:
        return {
            "UnnamedSingle": {
                "_0": bar_struct.BarStruct.to_encodable(self.value[0]),
            },
        }


class Named:
    discriminator = 2
    kind = "Named"

    def __init__(self, value: NamedFields) -> None:
        self.value: NamedValue = {
            "bool_field": value["bool_field"],
            "u8_field": value["u8_field"],
            "nested": bar_struct.BarStruct(**value["nested"]),
        }

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
                "nested": bar_struct.BarStruct.to_encodable(self.value["nested"]),
            },
        }


class Struct:
    discriminator = 3
    kind = "Struct"

    def __init__(self, value: StructFields) -> None:
        self.value: StructValue = (bar_struct.BarStruct(**value[0]),)

    def to_json(self) -> StructJSON:
        return StructJSON(
            kind="Struct",
            value=(self.value[0].to_json(),),
        )

    def to_encodable(self) -> dict:
        return {
            "Struct": {
                "_0": bar_struct.BarStruct.to_encodable(self.value[0]),
            },
        }


class OptionStruct:
    discriminator = 4
    kind = "OptionStruct"

    def __init__(self, value: OptionStructFields) -> None:
        self.value: OptionStructValue = (
            (value[0] and bar_struct.BarStruct(**value[0])) or None,
        )

    def to_json(self) -> OptionStructJSON:
        return OptionStructJSON(
            kind="OptionStruct",
            value=((self.value[0] and self.value[0].to_json()) or None,),
        )

    def to_encodable(self) -> dict:
        return {
            "OptionStruct": {
                "_0": (
                    self.value[0] and bar_struct.BarStruct.to_encodable(self.value[0])
                )
                or None,
            },
        }


class VecStruct:
    discriminator = 5
    kind = "VecStruct"

    def __init__(self, value: VecStructFields) -> None:
        self.value: VecStructValue = (
            list(map(lambda item: bar_struct.BarStruct(**item), value[0])),
        )

    def to_json(self) -> VecStructJSON:
        return VecStructJSON(
            kind="VecStruct",
            value=(list(map(lambda item: item.to_json(), self.value[0])),),
        )

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


class NoFields:
    discriminator = 6
    kind = "NoFields"

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
                val["_0"],
                val["_1"],
                bar_struct.BarStruct.from_decoded(val["_2"]),
            )
        )
    if "UnnamedSingle" in obj:
        val = obj["UnnamedSingle"]
        return UnnamedSingle((bar_struct.BarStruct.from_decoded(val["_0"]),))
    if "Named" in obj:
        val = obj["Named"]
        return Named(
            {
                "bool_field": val["bool_field"],
                "u8_field": val["u8_field"],
                "nested": bar_struct.BarStruct.from_decoded(val["nested"]),
            }
        )
    if "Struct" in obj:
        val = obj["Struct"]
        return Struct((bar_struct.BarStruct.from_decoded(val["_0"]),))
    if "OptionStruct" in obj:
        val = obj["OptionStruct"]
        return OptionStruct(
            ((val["_0"] and bar_struct.BarStruct.from_decoded(val["_0"])) or None,)
        )
    if "VecStruct" in obj:
        val = obj["VecStruct"]
        return VecStruct(
            (
                list(
                    map(lambda item: bar_struct.BarStruct.from_decoded(item), val["_0"])
                ),
            )
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
        return UnnamedSingle((bar_struct.BarStruct.from_json(obj["value[0]"]),))
    if obj["kind"] == "Named":
        return Named(
            {
                "bool_field": obj["value"]["bool_field"],
                "u8_field": obj["value"]["u8_field"],
                "nested": bar_struct.BarStruct.from_json(obj["value"]["nested"]),
            }
        )
    if obj["kind"] == "Struct":
        return Struct((bar_struct.BarStruct.from_json(obj["value[0]"]),))
    if obj["kind"] == "OptionStruct":
        return OptionStruct(
            (
                (obj["value[0]"] and bar_struct.BarStruct.from_json(obj["value[0]"]))
                or None,
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
