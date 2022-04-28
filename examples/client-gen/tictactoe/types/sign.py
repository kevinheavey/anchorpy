import typing
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class XJSON(typing.TypedDict):
    kind: typing.Literal["X"]


class OJSON(typing.TypedDict):
    kind: typing.Literal["O"]


class X(object):
    discriminator = 0
    kind = "X"

    @classmethod
    def to_json(cls) -> XJSON:
        return {
            "kind": "X",
        }

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "X": {},
        }


class O(object):
    discriminator = 1
    kind = "O"

    @classmethod
    def to_json(cls) -> OJSON:
        return {
            "kind": "O",
        }

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
    raise ValueError(f"Uncrecognized enum kind: {kind}")


layout = EnumForCodegen("X" / borsh.CStruct(), "O" / borsh.CStruct())
