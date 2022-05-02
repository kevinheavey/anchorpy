from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class XJSON(typing.TypedDict):
    kind: typing.Literal["X"]


class OJSON(typing.TypedDict):
    kind: typing.Literal["O"]


@dataclass
class X:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "X"

    @classmethod
    def to_json(cls) -> XJSON:
        return XJSON(
            kind="X",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "X": {},
        }


@dataclass
class O:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "O"

    @classmethod
    def to_json(cls) -> OJSON:
        return OJSON(
            kind="O",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "O": {},
        }


SignKind = typing.Union[X, O]
SignJSON = typing.Union[XJSON, OJSON]


def from_decoded(obj: dict) -> SignKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "X" in obj:
        return X()
    if "O" in obj:
        return O()
    raise ValueError("Invalid enum object")


def from_json(obj: SignJSON) -> SignKind:
    if obj["kind"] == "X":
        return X()
    if obj["kind"] == "O":
        return O()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("X" / borsh.CStruct(), "O" / borsh.CStruct())
