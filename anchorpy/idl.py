from dataclasses import dataclass, field
from typing import List, Union, Optional, Dict, Any, Literal, Tuple

from apischema import deserialize, alias

LiteralStrings = Union[
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
]
NonLiteralIdlTypes = Union[
    "IdlTypeVec", "IdlTypeOption", "IdlTypeDefined", "IdlTypeArray"
]
IdlType = Union[LiteralStrings, NonLiteralIdlTypes]


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
    name: str
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


IdlAccountItem = Union[IdlAccounts, IdlAccount]


@dataclass
class IdlInstruction:
    name: str
    accounts: List[IdlAccountItem]
    args: List[IdlField]


IdlEnumFieldsNamed = List[IdlField]
IdlEnumFieldsTuple = List[IdlType]
IdlEnumFields = Union[IdlEnumFieldsNamed, IdlEnumFieldsTuple]


@dataclass
class IdlEnumVariant:
    name: str
    fields: Optional[IdlEnumFields] = None


IdlTypeDefStruct = List[IdlField]


@dataclass
class IdlTypeDefTyStruct:
    fields: IdlTypeDefStruct
    kind: Literal["struct"] = "struct"


@dataclass
class IdlTypeDefTyEnum:
    variants: List[IdlEnumVariant]
    kind: Literal["enum"] = "enum"


IdlTypeDefTy = Union[IdlTypeDefTyEnum, IdlTypeDefTyStruct]


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
    type: IdlType
    index: bool


@dataclass
class IdlEvent:
    name: str
    fields: List[IdlEventField]


@dataclass
class IdlErrorCode:
    code: int
    name: str
    msg: Optional[str] = None


@dataclass
class Metadata:
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
