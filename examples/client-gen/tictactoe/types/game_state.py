import typing
from solana.publickey import PublicKey
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class WonJSONValue(typing.TypedDict):
    winner: str


class WonFields(typing.TypedDict):
    winner: PublicKey


class WonValue(typing.TypedDict):
    winner: PublicKey


class ActiveJSON(typing.TypedDict):
    kind: typing.Literal["Active"]


class TieJSON(typing.TypedDict):
    kind: typing.Literal["Tie"]


class WonJSON(typing.TypedDict):
    value: WonJSONValue
    kind: typing.Literal["Won"]


class Active(object):
    discriminator = 0
    kind = "Active"

    @classmethod
    def to_json(cls) -> ActiveJSON:
        return {
            "kind": "Active",
        }

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Active": {},
        }


class Tie(object):
    discriminator = 1
    kind = "Tie"

    @classmethod
    def to_json(cls) -> TieJSON:
        return {
            "kind": "Tie",
        }

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Tie": {},
        }


class Won(object):
    discriminator = 2
    kind = "Won"

    def __init__(self, value: WonFields) -> None:
        self.value = {
            "winner": value["winner"],
        }

    def to_json(self) -> WonJSON:
        return {
            "kind": "Won",
            "value": {
                "winner": self.value["winner"].to_base58(),
            },
        }

    def to_encodable(self) -> dict:
        return {
            "Won": {
                "winner": self.value["winner"],
            },
        }


GameStateKind = typing.Union[Active, Tie, Won]
GameStateJSON = typing.Union[ActiveJSON, TieJSON, WonJSON]


def from_decoded(obj: dict) -> GameStateKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Active" in obj:
        return Active()
    if "Tie" in obj:
        return Tie()
    if "Won" in obj:
        val = obj["Won"]
        return Won(
            {
                "winner": val["winner"],
            }
        )
    raise ValueError("Invalid enum object")


def from_json(obj: GameStateJSON) -> GameStateKind:
    kind = obj["kind"]
    if kind == "Active":
        return Active()
    if kind == "Tie":
        return Tie()
    if kind == "Won":
        return Won(
            {
                "winner": PublicKey(obj["value"]["winner"]),
            }
        )
    raise ValueError(f"Uncrecognized enum kind: {kind}")


def layout() -> EnumForCodegen:
    return EnumForCodegen(
        "Active" / borsh.CStruct(),
        "Tie" / borsh.CStruct(),
        "Won" / borsh.CStruct("winner" / BorshPubkey),
    )
