from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class TileJSON(typing.TypedDict):
    row: int
    column: int


@dataclass
class Tile:
    layout: typing.ClassVar = borsh.CStruct("row" / borsh.U8, "column" / borsh.U8)
    row: int
    column: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "Tile":
        return cls(row=obj.row, column=obj.column)

    def to_encodable(self) -> dict[str, typing.Any]:
        return {"row": self.row, "column": self.column}

    def to_json(self) -> TileJSON:
        return {"row": self.row, "column": self.column}

    @classmethod
    def from_json(cls, obj: TileJSON) -> "Tile":
        return cls(row=obj["row"], column=obj["column"])
