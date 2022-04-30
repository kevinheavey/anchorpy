from __future__ import annotations
from . import bar_struct, foo_enum
import typing
from construct import Container
import borsh_construct as borsh


class FooStructFields(typing.TypedDict):
    field1: int
    field2: int
    nested: bar_struct.BarStructFields
    vec_nested: list[bar_struct.BarStructFields]
    option_nested: typing.Optional[bar_struct.BarStructFields]
    enum_field: foo_enum.FooEnumKind


class FooStructJSON(typing.TypedDict):
    field1: int
    field2: int
    nested: bar_struct.BarStructJSON
    vec_nested: list[bar_struct.BarStructJSON]
    option_nested: typing.Optional[bar_struct.BarStructJSON]
    enum_field: foo_enum.FooEnumJSON


class FooStruct:
    layout = borsh.CStruct(
        "field1" / borsh.U8,
        "field2" / borsh.U16,
        "nested" / bar_struct.BarStruct.layout,
        "vec_nested" / borsh.Vec(bar_struct.BarStruct.layout),
        "option_nested" / borsh.Option(bar_struct.BarStruct.layout),
        "enum_field" / foo_enum.layout,
    )

    def __init__(self, fields: FooStructFields) -> None:
        self.field1 = fields["field1"]
        self.field2 = fields["field2"]
        self.nested = bar_struct.BarStruct(**fields["nested"])
        self.vec_nested = list(
            map(lambda item: bar_struct.BarStruct(**item), fields["vec_nested"])
        )
        self.option_nested = (
            fields["option_nested"] and bar_struct.BarStruct(**fields["option_nested"])
        ) or None
        self.enum_field = fields["enum_field"]

    @classmethod
    def from_decoded(cls, obj: Container) -> "FooStruct":
        return cls(
            FooStructFields(
                field1=obj.field1,
                field2=obj.field2,
                nested=bar_struct.BarStruct.from_decoded(obj.nested),
                vec_nested=list(
                    map(
                        lambda item: bar_struct.BarStruct.from_decoded(item),
                        obj.vec_nested,
                    )
                ),
                option_nested=(
                    obj.option_nested
                    and bar_struct.BarStruct.from_decoded(obj.option_nested)
                )
                or None,
                enum_field=foo_enum.from_decoded(obj.enum_field),
            )
        )

    @classmethod
    def to_encodable(cls, fields: FooStructFields) -> dict[str, typing.Any]:
        return {
            "field1": fields["field1"],
            "field2": fields["field2"],
            "nested": bar_struct.BarStruct.to_encodable(fields["nested"]),
            "vec_nested": list(
                map(
                    lambda item: bar_struct.BarStruct.to_encodable(item),
                    fields["vec_nested"],
                )
            ),
            "option_nested": (
                fields["option_nested"]
                and bar_struct.BarStruct.to_encodable(fields["option_nested"])
            )
            or None,
            "enum_field": fields["enum_field"].to_encodable(),
        }

    def to_json(self) -> FooStructJSON:
        return {
            "field1": self.field1,
            "field2": self.field2,
            "nested": self.nested.to_json(),
            "vec_nested": list(map(lambda item: item.to_json(), self.vec_nested)),
            "option_nested": (self.option_nested and self.option_nested.to_json())
            or None,
            "enum_field": self.enum_field.to_json(),
        }

    @classmethod
    def from_json(cls, obj: FooStructJSON) -> "FooStruct":
        return cls(
            FooStructJSON(
                field1=obj["field1"],
                field2=obj["field2"],
                nested=bar_struct.BarStruct.from_json(obj["nested"]),
                vec_nested=list(
                    map(
                        lambda item: bar_struct.BarStruct.from_json(item),
                        obj["vec_nested"],
                    )
                ),
                option_nested=(
                    obj["option_nested"]
                    and bar_struct.BarStruct.from_json(obj["option_nested"])
                )
                or None,
                enum_field=foo_enum.from_json(obj["enum_field"]),
            )
        )
