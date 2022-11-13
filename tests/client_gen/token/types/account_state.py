from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class UninitializedJSON(typing.TypedDict):
    kind: typing.Literal["Uninitialized"]


class InitializedJSON(typing.TypedDict):
    kind: typing.Literal["Initialized"]


class FrozenJSON(typing.TypedDict):
    kind: typing.Literal["Frozen"]


@dataclass
class Uninitialized:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Uninitialized"

    @classmethod
    def to_json(cls) -> UninitializedJSON:
        return UninitializedJSON(
            kind="Uninitialized",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Uninitialized": {},
        }


@dataclass
class Initialized:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Initialized"

    @classmethod
    def to_json(cls) -> InitializedJSON:
        return InitializedJSON(
            kind="Initialized",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Initialized": {},
        }


@dataclass
class Frozen:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "Frozen"

    @classmethod
    def to_json(cls) -> FrozenJSON:
        return FrozenJSON(
            kind="Frozen",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Frozen": {},
        }


AccountStateKind = typing.Union[Uninitialized, Initialized, Frozen]
AccountStateJSON = typing.Union[UninitializedJSON, InitializedJSON, FrozenJSON]


def from_decoded(obj: dict) -> AccountStateKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Uninitialized" in obj:
        return Uninitialized()
    if "Initialized" in obj:
        return Initialized()
    if "Frozen" in obj:
        return Frozen()
    raise ValueError("Invalid enum object")


def from_json(obj: AccountStateJSON) -> AccountStateKind:
    if obj["kind"] == "Uninitialized":
        return Uninitialized()
    if obj["kind"] == "Initialized":
        return Initialized()
    if obj["kind"] == "Frozen":
        return Frozen()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Uninitialized" / borsh.CStruct(),
    "Initialized" / borsh.CStruct(),
    "Frozen" / borsh.CStruct(),
)
