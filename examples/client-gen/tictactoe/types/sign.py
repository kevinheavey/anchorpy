import typing
from dataclasses import dataclass
from construct import Container
from solana.publickey import PublicKey
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh
from .. import types
class XJSON(typing.TypedDict):
    kind: typing.Literal["X"]
class OJSON(typing.TypedDict):
    kind: typing.Literal["O"]
class X(object):
    discriminator = 0
    kind = "X"
    @classmethod
    def to_json(cls) -> XJSON:
        return {"kind": "X",}
    @classmethod
    def to_encodable(cls) -> dict:
        return {"X": {},}
class O(object):
    discriminator = 1
    kind = "O"
    @classmethod
    def to_json(cls) -> OJSON:
        return {"kind": "O",}
    @classmethod
    def to_encodable(cls) -> dict:
        return {"O": {},}
def from_decoded(obj: dict) -> types.SignKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "X" in obj:
        return X()
    if "O" in obj:
        return O()
    raise ValueError("Invalid enum object")
def from_json(obj: types.SignJSON) -> types.SignKind:
    kind = obj["kind"]
    if kind == "X":
        return X()
    if kind == "O":
        return O()
    raise ValueError(f"Uncrecognized enum kind: {kind}")
def layout() -> EnumForCodegen:
    return EnumForCodegen("X" / borsh.CStruct(),"O" / borsh.CStruct())