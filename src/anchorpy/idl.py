from dataclasses import dataclass, field
from typing import List, Union, Optional, Dict, Any, Literal, Tuple, TypedDict

from apischema import deserialize, alias
from apischema.metadata import conversion
from inflection import underscore, camelize
from borsh_construct import CStruct, Vec, U8
import solana.publickey  # noqa: WPS301

from anchorpy import borsh_extension


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
snake_case_conversion = conversion(underscore, camelize)


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
    name: str = field(metadata=snake_case_conversion)
    type: IdlType


@dataclass
class IdlAccount:
    name: str = field(metadata=snake_case_conversion)
    is_mut: bool = field(metadata=alias("isMut"))
    is_signer: bool = field(metadata=alias("isSigner"))


@dataclass
class IdlAccounts:
    # Nested/recursive version of IdlAccount
    name: str = field(metadata=snake_case_conversion)
    accounts: List["IdlAccountItem"]


IdlAccountItem = Union[IdlAccounts, IdlAccount]


@dataclass
class IdlInstruction:
    name: str = field(metadata=snake_case_conversion)
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


IdlStateMethod = IdlInstruction


@dataclass
class IdlState:
    struct: IdlTypeDef
    methods: List[IdlStateMethod]


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
    state: Optional[IdlState] = None
    accounts: List[IdlTypeDef] = field(default_factory=list)
    types: List[IdlTypeDef] = field(default_factory=list)
    events: List[IdlEvent] = field(default_factory=list)
    errors: List[IdlErrorCode] = field(default_factory=list)
    metadata: Optional[Metadata] = None

    @classmethod
    def from_json(cls, idl: Dict[str, Any]) -> "Idl":
        return deserialize(cls, idl)


SEED = "anchor:idl"


def idl_address(program_id: solana.publickey.PublicKey) -> solana.publickey.PublicKey:
    """Deterministic IDL address as a function of the program id."""
    base = solana.publickey.PublicKey.find_program_address([], program_id)[0]
    return solana.publickey.PublicKey.create_with_seed(base, SEED, program_id)


class IdlProgramAccount(TypedDict):
    """The on-chain account of the IDL."""

    authority: solana.publickey.PublicKey
    data: bytes


IDL_ACCOUNT_LAYOUT = CStruct("authority" / borsh_extension.PublicKey, "data" / Vec(U8))


def decode_idl_account(data: bytes) -> IdlProgramAccount:
    return IDL_ACCOUNT_LAYOUT.parse(data)


def encode_idl_account(acc: IdlProgramAccount) -> bytes:
    return IDL_ACCOUNT_LAYOUT.build(acc)
