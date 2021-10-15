from dataclasses import dataclass, field
from typing import List, Union, Optional, Dict, Any, Literal, Tuple

from apischema import deserialize, alias


LiteralStrings = Literal[
    "bool",
    "u8",
    "i8",
    "u16",
    "i16",
    "u32",
    "i32",
    "u64",
    "i64",
    "u128",
    "i128",
    "bytes",
    "string",
    "publicKey",
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
    """A parsed IDL object."""

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
