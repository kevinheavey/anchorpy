from dataclasses import dataclass, field
from typing import List, Union, Optional, Dict, Any, Literal, Tuple

from apischema import deserialize, alias
from apischema.conversions import as_str
from solana import publickey

as_str(publickey.PublicKey)


IdlType = Union[
    Literal["bool"],
    Literal["u8"],
    Literal["i8"],
    Literal["u16"],
    Literal["i16"],
    Literal["u32"],
    Literal["i32"],
    Literal["u64"],
    Literal["i64"],
    Literal["u128"],
    Literal["i128"],
    Literal["bytes"],
    Literal["string"],
    Literal["publicKey"],
    "IdlTypeVec",
    "IdlTypeOption",
    "IdlTypeDefined",
    "IdlTypeArray",
]


@dataclass
class IdlTypeVec:
    vec: IdlType


@dataclass
class IdlTypeOption:
    option: IdlType


@dataclass
class IdlTypeDefined:
    defined: str


@dataclass
class IdlField:
    name: Optional[str]
    type: IdlType


@dataclass
class IdlAccount:
    name: str
    is_mut: bool = field(metadata=alias("isMut"))
    is_signer: bool = field(metadata=alias("isSigner"))


@dataclass
class IdlAccounts:
    # Nested/recursive version of IdlAccount
    name: str
    accounts: List["IdlAccountItem"]


# @dataclass
# class IdlAccounts0:
#     name: str
#     accounts: List[IdlAccount]


# @dataclass
# class IdlAccounts1:
#     name: str
#     accounts: List[Union[IdlAccount, IdlAccounts0]]


# class IdlAccounts2:
#     name: str
#     accounts: List[Union[IdlAccount, IdlAccounts0, IdlAccounts1]]


# IdlAccounts = Union[IdlAccounts2, IdlAccounts1, IdlAccounts0]
IdlAccountItem = Union[IdlAccounts, IdlAccount]


@dataclass
class IdlInstruction:
    name: str
    accounts: List[IdlAccountItem]
    args: List[IdlField]


@dataclass
class IdlEnumVariant:
    name: str
    fields: Optional[Union[List[IdlField], List[IdlType]]] = None


@dataclass
class IdlTypeDefTy:
    kind: str
    fields: Optional[List[IdlField]] = None
    variants: Optional[List[IdlEnumVariant]] = None


@dataclass
class IdlTypeDef:
    name: str
    type: IdlTypeDefTy


@dataclass
class IdlTypeArray:
    array: Tuple[IdlType, int]


@dataclass
class IdlEventField:
    name: str
    type: str
    index: bool


@dataclass
class IdlEvent:
    name: str
    fields: List[IdlEventField]


@dataclass
class IdlErrorCode:
    code: int
    name: str
    msg: str = ""


@dataclass
class Metadata:
    # address: publickey.PublicKey
    address: str


@dataclass
class Idl:
    version: str
    name: str
    instructions: List[IdlInstruction]
    accounts: List[IdlTypeDef] = field(default_factory=list)
    types: List[IdlTypeDef] = field(default_factory=list)
    events: List[IdlEvent] = field(default_factory=list)
    errors: List[IdlErrorCode] = field(default_factory=list)
    metadata: Optional[Metadata] = None

    @classmethod
    def from_json(cls, idl: Dict[str, Any]) -> "Idl":
        return deserialize(cls, idl)


if __name__ == "__main__":
    import json
    from pathlib import Path

    with Path("/home/kheavey/anchorpy/idls/chat.json").open() as f:
        data = json.load(f)
    for path in Path("/home/kheavey/anchorpy/idls/").glob("*"):
        print(path)
        with path.open() as f:
            data = json.load(f)
        idl = Idl.from_json(data)
    defined = deserialize(IdlTypeDefined, {"defined": "Message"})
    arr = deserialize(IdlTypeArray, {"array": [{"defined": "Message"}, 33607]})
    idl = Idl.from_json(data)
    breakpoint()
