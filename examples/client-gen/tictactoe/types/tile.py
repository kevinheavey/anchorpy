import typing
from dataclasses import dataclass
from construct import Container
from solana.publickey import PublicKey
import borsh_construct as borsh


class TileFields(typing.TypedDict):
    row: int
    column: int


class TileJSON(typing.TypedDict):
    row: int
    column: int


class Tile(object):
    def __init__(self, fields: TileFields) -> None:
        self.row = fields["row"]
        self.column = fields["column"]

    @staticmethod
    def layout() -> borsh.CStruct:
        return borsh.CStruct("row" / borsh.U8, "column" / borsh.U8)

    @classmethod
    def from_decoded(cls, obj: Container) -> "Tile":
        return cls(TileFields(row=obj.row, column=obj.column))

    @classmethod
    def to_encodable(cls, fields: TileFields) -> dict[str, typing.Any]:
        return {"row": fields["row"], "column": fields["column"]}

    def to_json(self) -> TileJSON:
        return {"row": self.row, "column": self.column}

    @classmethod
    def from_json(cls, obj: TileJSON) -> "Tile":
        return cls(TileJSON(row=obj["row"], column=obj["column"]))
