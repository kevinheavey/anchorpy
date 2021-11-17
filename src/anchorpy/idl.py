"""Contains code for parsing the IDL file."""
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
    """IDL vector type."""

    vec: IdlType


@dataclass
class IdlTypeOption:
    """IDL option type."""

    option: IdlType


@dataclass
class IdlTypeDefined:
    """IDL type that points to a user-defined type."""

    defined: str


@dataclass
class IdlField:
    """IDL representation of a field.

    Used in instructions and user-defined types.
    """

    name: str = field(metadata=snake_case_conversion)
    type: IdlType


@dataclass
class IdlAccount:
    """IDL account type."""

    name: str = field(metadata=snake_case_conversion)
    is_mut: bool = field(metadata=alias("isMut"))
    is_signer: bool = field(metadata=alias("isSigner"))


@dataclass
class IdlAccounts:
    """Nested/recursive version of IdlAccount."""

    name: str = field(metadata=snake_case_conversion)
    accounts: List["IdlAccountItem"]


IdlAccountItem = Union[IdlAccounts, IdlAccount]


@dataclass
class IdlInstruction:
    """IDL representation of a program instruction."""

    name: str = field(metadata=snake_case_conversion)
    accounts: List[IdlAccountItem]
    args: List[IdlField]


IdlEnumFieldsNamed = List[IdlField]
IdlEnumFieldsTuple = List[IdlType]
IdlEnumFields = Union[IdlEnumFieldsNamed, IdlEnumFieldsTuple]


@dataclass
class IdlEnumVariant:
    """IDL representation of a variant of an enum."""

    name: str
    fields: Optional[IdlEnumFields] = None


IdlTypeDefStruct = List[IdlField]


@dataclass
class IdlTypeDefTyStruct:
    """IDL representation of a struct."""

    fields: IdlTypeDefStruct
    kind: Literal["struct"] = "struct"


@dataclass
class IdlTypeDefTyEnum:
    """IDL representation of an enum."""

    variants: List[IdlEnumVariant]
    kind: Literal["enum"] = "enum"


IdlTypeDefTy = Union[IdlTypeDefTyEnum, IdlTypeDefTyStruct]


@dataclass
class IdlTypeDef:
    """IDL representation of a user-defined type."""

    name: str
    type: IdlTypeDefTy


IdlStateMethod = IdlInstruction


@dataclass
class IdlState:
    """IDL representation of a program state method."""

    struct: IdlTypeDef
    methods: List[IdlStateMethod]


@dataclass
class IdlTypeArray:
    """IDL array type."""

    array: Tuple[IdlType, int]


@dataclass
class IdlEventField:
    """IDL representation of an event field."""

    name: str
    type: IdlType
    index: bool


@dataclass
class IdlEvent:
    """IDL representation of an event.

    Composed of a list of event fields.
    """

    name: str
    fields: List[IdlEventField]


@dataclass
class IdlErrorCode:
    """IDL error code type."""

    code: int
    name: str
    msg: Optional[str] = None


@dataclass
class Metadata:
    """IDL metadata field."""

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
        """Generate a parsed IDL from a JSON dict.

        Args:
            idl: The raw IDL dict.

        Returns:
            The parsed Idl object.
        """
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
    """Decode on-chain IDL.

    Args:
        data: binary data from the account that stores the IDL.

    Returns:
        Decoded IDL.
    """
    return IDL_ACCOUNT_LAYOUT.parse(data)


def encode_idl_account(acc: IdlProgramAccount) -> bytes:
    """Encode IDL for on-chain storage.

    Args:
        acc: data to encode.

    Returns:
        bytes: Encoded IDL.
    """
    return IDL_ACCOUNT_LAYOUT.build(acc)
