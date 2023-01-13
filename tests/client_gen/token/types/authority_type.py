from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class MintTokensJSON(typing.TypedDict):
    kind: typing.Literal["MintTokens"]


class FreezeAccountJSON(typing.TypedDict):
    kind: typing.Literal["FreezeAccount"]


class AccountOwnerJSON(typing.TypedDict):
    kind: typing.Literal["AccountOwner"]


class CloseAccountJSON(typing.TypedDict):
    kind: typing.Literal["CloseAccount"]


@dataclass
class MintTokens:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "MintTokens"

    @classmethod
    def to_json(cls) -> MintTokensJSON:
        return MintTokensJSON(
            kind="MintTokens",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "MintTokens": {},
        }


@dataclass
class FreezeAccount:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "FreezeAccount"

    @classmethod
    def to_json(cls) -> FreezeAccountJSON:
        return FreezeAccountJSON(
            kind="FreezeAccount",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "FreezeAccount": {},
        }


@dataclass
class AccountOwner:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "AccountOwner"

    @classmethod
    def to_json(cls) -> AccountOwnerJSON:
        return AccountOwnerJSON(
            kind="AccountOwner",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "AccountOwner": {},
        }


@dataclass
class CloseAccount:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "CloseAccount"

    @classmethod
    def to_json(cls) -> CloseAccountJSON:
        return CloseAccountJSON(
            kind="CloseAccount",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "CloseAccount": {},
        }


AuthorityTypeKind = typing.Union[MintTokens, FreezeAccount, AccountOwner, CloseAccount]
AuthorityTypeJSON = typing.Union[
    MintTokensJSON, FreezeAccountJSON, AccountOwnerJSON, CloseAccountJSON
]


def from_decoded(obj: dict) -> AuthorityTypeKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "MintTokens" in obj:
        return MintTokens()
    if "FreezeAccount" in obj:
        return FreezeAccount()
    if "AccountOwner" in obj:
        return AccountOwner()
    if "CloseAccount" in obj:
        return CloseAccount()
    raise ValueError("Invalid enum object")


def from_json(obj: AuthorityTypeJSON) -> AuthorityTypeKind:
    if obj["kind"] == "MintTokens":
        return MintTokens()
    if obj["kind"] == "FreezeAccount":
        return FreezeAccount()
    if obj["kind"] == "AccountOwner":
        return AccountOwner()
    if obj["kind"] == "CloseAccount":
        return CloseAccount()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "MintTokens" / borsh.CStruct(),
    "FreezeAccount" / borsh.CStruct(),
    "AccountOwner" / borsh.CStruct(),
    "CloseAccount" / borsh.CStruct(),
)
