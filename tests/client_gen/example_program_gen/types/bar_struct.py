from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class BarStructJSON(typing.TypedDict):
    some_field: bool
    other_field: int


@dataclass
class BarStruct:
    layout: typing.ClassVar = borsh.CStruct(
        "some_field" / borsh.Bool, "other_field" / borsh.U8
    )
    some_field: bool
    other_field: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "BarStruct":
        return cls(some_field=obj.some_field, other_field=obj.other_field)

    def to_encodable(self) -> dict[str, typing.Any]:
        return {"some_field": self.some_field, "other_field": self.other_field}

    def to_json(self) -> BarStructJSON:
        return {"some_field": self.some_field, "other_field": self.other_field}

    @classmethod
    def from_json(cls, obj: BarStructJSON) -> "BarStruct":
        return cls(some_field=obj["some_field"], other_field=obj["other_field"])
