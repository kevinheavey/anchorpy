from __future__ import annotations
from . import bar_struct, foo_enum
import typing
from dataclasses import dataclass
from construct import Container, Construct
import borsh_construct as borsh


class FooStructJSON(typing.TypedDict):
    field1: int
    field2: int
    nested: bar_struct.BarStructJSON
    vec_nested: list[bar_struct.BarStructJSON]
    option_nested: typing.Optional[bar_struct.BarStructJSON]
    enum_field: foo_enum.FooEnumJSON


@dataclass
class FooStruct:
    layout: typing.ClassVar = borsh.CStruct(
        "field1" / borsh.U8,
        "field2" / borsh.U16,
        "nested" / bar_struct.BarStruct.layout,
        "vec_nested" / borsh.Vec(typing.cast(Construct, bar_struct.BarStruct.layout)),
        "option_nested" / borsh.Option(bar_struct.BarStruct.layout),
        "enum_field" / foo_enum.layout,
    )
    field1: int
    field2: int
    nested: bar_struct.BarStruct
    vec_nested: list[bar_struct.BarStruct]
    option_nested: typing.Optional[bar_struct.BarStruct]
    enum_field: foo_enum.FooEnumKind

    @classmethod
    def from_decoded(cls, obj: Container) -> "FooStruct":
        return cls(
            field1=obj.field1,
            field2=obj.field2,
            nested=bar_struct.BarStruct.from_decoded(obj.nested),
            vec_nested=list(
                map(
                    lambda item: bar_struct.BarStruct.from_decoded(item), obj.vec_nested
                )
            ),
            option_nested=(
                None
                if obj.option_nested is None
                else bar_struct.BarStruct.from_decoded(obj.option_nested)
            ),
            enum_field=foo_enum.from_decoded(obj.enum_field),
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "field1": self.field1,
            "field2": self.field2,
            "nested": self.nested.to_encodable(),
            "vec_nested": list(map(lambda item: item.to_encodable(), self.vec_nested)),
            "option_nested": (
                None
                if self.option_nested is None
                else self.option_nested.to_encodable()
            ),
            "enum_field": self.enum_field.to_encodable(),
        }

    def to_json(self) -> FooStructJSON:
        return {
            "field1": self.field1,
            "field2": self.field2,
            "nested": self.nested.to_json(),
            "vec_nested": list(map(lambda item: item.to_json(), self.vec_nested)),
            "option_nested": (
                None if self.option_nested is None else self.option_nested.to_json()
            ),
            "enum_field": self.enum_field.to_json(),
        }

    @classmethod
    def from_json(cls, obj: FooStructJSON) -> "FooStruct":
        return cls(
            field1=obj["field1"],
            field2=obj["field2"],
            nested=bar_struct.BarStruct.from_json(obj["nested"]),
            vec_nested=list(
                map(
                    lambda item: bar_struct.BarStruct.from_json(item), obj["vec_nested"]
                )
            ),
            option_nested=(
                None
                if obj["option_nested"] is None
                else bar_struct.BarStruct.from_json(obj["option_nested"])
            ),
            enum_field=foo_enum.from_json(obj["enum_field"]),
        )
