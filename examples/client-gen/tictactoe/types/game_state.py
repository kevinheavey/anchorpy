from __future__ import annotations
import typing
from solana.publickey import PublicKey
from anchorpy.borsh_extension import EnumForCodegen, BorshPubkey
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


class Active:
    discriminator = 0
    kind = "Active"

    @classmethod
    def to_json(cls) -> ActiveJSON:
        return ActiveJSON(
            kind="Active",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Active": {},
        }


class Tie:
    discriminator = 1
    kind = "Tie"

    @classmethod
    def to_json(cls) -> TieJSON:
        return TieJSON(
            kind="Tie",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Tie": {},
        }


class Won:
    discriminator = 2
    kind = "Won"

    def __init__(self, value: WonFields) -> None:
        self.value: WonValue = {
            "winner": value["winner"],
        }

    def to_json(self) -> WonJSON:
        return WonJSON(
            kind="Won",
            value={
                "winner": str(self.value["winner"]),
            },
        )

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
    if obj["kind"] == "Active":
        return Active()
    if obj["kind"] == "Tie":
        return Tie()
    if obj["kind"] == "Won":
        return Won(
            {
                "winner": PublicKey(obj["value"]["winner"]),
            }
        )
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Active" / borsh.CStruct(),
    "Tie" / borsh.CStruct(),
    "Won" / borsh.CStruct("winner" / BorshPubkey),
)
