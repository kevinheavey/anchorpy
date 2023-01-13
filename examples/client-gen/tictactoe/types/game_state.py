from __future__ import annotations
import typing
from dataclasses import dataclass
from solders.pubkey import Pubkey
from anchorpy.borsh_extension import EnumForCodegen, BorshPubkey
import borsh_construct as borsh


class WonJSONValue(typing.TypedDict):
    winner: str


class WonValue(typing.TypedDict):
    winner: Pubkey


class ActiveJSON(typing.TypedDict):
    kind: typing.Literal["Active"]


class TieJSON(typing.TypedDict):
    kind: typing.Literal["Tie"]


class WonJSON(typing.TypedDict):
    value: WonJSONValue
    kind: typing.Literal["Won"]


@dataclass
class Active:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Active"

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


@dataclass
class Tie:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Tie"

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


@dataclass
class Won:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "Won"
    value: WonValue

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
            WonValue(
                winner=val["winner"],
            )
        )
    raise ValueError("Invalid enum object")


def from_json(obj: GameStateJSON) -> GameStateKind:
    if obj["kind"] == "Active":
        return Active()
    if obj["kind"] == "Tie":
        return Tie()
    if obj["kind"] == "Won":
        won_json_value = typing.cast(WonJSONValue, obj["value"])
        return Won(
            WonValue(
                winner=Pubkey.from_string(won_json_value["winner"]),
            )
        )
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Active" / borsh.CStruct(),
    "Tie" / borsh.CStruct(),
    "Won" / borsh.CStruct("winner" / BorshPubkey),
)
