"""Contains code for parsing the IDL file."""
from dataclasses import dataclass, field
from typing import List, Union, Optional, Dict, Any, Literal, Tuple, TypedDict

from apischema import deserialize, alias
from apischema.metadata import conversion
from inflection import underscore, camelize
from borsh_construct import CStruct, Vec, U8
import solana.publickey  # noqa: WPS301

from anchorpy.borsh_extension import _BorshPubkey

_LiteralStrings = Literal[
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
_NonLiteralIdlTypes = Union[
    "_IdlTypeVec", "_IdlTypeOption", "_IdlTypeDefined", "_IdlTypeArray"
]
_IdlType = Union[_NonLiteralIdlTypes, _LiteralStrings]
snake_case_conversion = conversion(underscore, camelize)


@dataclass
class _IdlTypeVec:
    """IDL vector type."""

    vec: _IdlType


@dataclass
class _IdlTypeOption:
    """IDL option type."""

    option: _IdlType


@dataclass
class _IdlTypeDefined:
    """IDL type that points to a user-defined type."""

    defined: str


@dataclass
class _IdlField:
    """IDL representation of a field.

    Used in instructions and user-defined types.
    """

    name: str = field(metadata=snake_case_conversion)
    type: _IdlType


@dataclass
class _IdlAccount:
    """IDL account type."""

    name: str = field(metadata=snake_case_conversion)
    is_mut: bool = field(metadata=alias("isMut"))
    is_signer: bool = field(metadata=alias("isSigner"))


@dataclass
class _IdlAccounts:
    """Nested/recursive version of _IdlAccount."""

    name: str = field(metadata=snake_case_conversion)
    accounts: List["_IdlAccountItem"]


_IdlAccountItem = Union[_IdlAccounts, _IdlAccount]


@dataclass
class _IdlInstruction:
    """IDL representation of a program instruction."""

    name: str = field(metadata=snake_case_conversion)
    accounts: List[_IdlAccountItem]
    args: List[_IdlField]


_IdlEnumFieldsNamed = List[_IdlField]
_IdlEnumFieldsTuple = List[_IdlType]
_IdlEnumFields = Union[_IdlEnumFieldsNamed, _IdlEnumFieldsTuple]


@dataclass
class _IdlEnumVariant:
    """IDL representation of a variant of an enum."""

    name: str
    fields: Optional[_IdlEnumFields] = None


_IdlTypeDefStruct = List[_IdlField]


@dataclass
class _IdlTypeDefTyStruct:
    """IDL representation of a struct."""

    fields: _IdlTypeDefStruct
    kind: Literal["struct"] = "struct"


@dataclass
class _IdlTypeDefTyEnum:
    """IDL representation of an enum."""

    variants: List[_IdlEnumVariant]
    kind: Literal["enum"] = "enum"


_IdlTypeDefTy = Union[_IdlTypeDefTyEnum, _IdlTypeDefTyStruct]


@dataclass
class _IdlTypeDef:
    """IDL representation of a user-defined type."""

    name: str
    type: _IdlTypeDefTy


_IdlStateMethod = _IdlInstruction


@dataclass
class _IdlState:
    """IDL representation of a program state method."""

    struct: _IdlTypeDef
    methods: List[_IdlStateMethod]


@dataclass
class _IdlTypeArray:
    """IDL array type."""

    array: Tuple[_IdlType, int]


@dataclass
class _IdlEventField:
    """IDL representation of an event field."""

    name: str
    type: _IdlType
    index: bool


@dataclass
class _IdlConstant:
    """IDL representation of a constant value."""

    name: str
    type: _IdlType
    value: str


@dataclass
class _IdlEvent:
    """IDL representation of an event.

    Composed of a list of event fields.
    """

    name: str
    fields: List[_IdlEventField]


@dataclass
class _IdlErrorCode:
    """IDL error code type."""

    code: int
    name: str
    msg: Optional[str] = None


@dataclass
class _Metadata:
    """IDL metadata field."""

    address: str


@dataclass
class Idl:
    """A parsed IDL object."""

    version: str
    name: str
    instructions: List[_IdlInstruction]
    state: Optional[_IdlState] = None
    accounts: List[_IdlTypeDef] = field(default_factory=list)
    types: List[_IdlTypeDef] = field(default_factory=list)
    events: List[_IdlEvent] = field(default_factory=list)
    errors: List[_IdlErrorCode] = field(default_factory=list)
    constants: List[_IdlConstant] = field(default_factory=list)
    metadata: Optional[_Metadata] = None

    @classmethod
    def from_json(cls, idl: Dict[str, Any]) -> "Idl":
        """Generate a parsed IDL from a JSON dict.

        Args:
            idl: The raw IDL dict.

        Returns:
            The parsed Idl object.
        """
        return deserialize(cls, idl)


def _idl_address(program_id: solana.publickey.PublicKey) -> solana.publickey.PublicKey:
    """Deterministic IDL address as a function of the program id.

    Args:
        program_id: The program ID.

    Returns:
        The public key of the IDL.
    """
    base = solana.publickey.PublicKey.find_program_address([], program_id)[0]
    return solana.publickey.PublicKey.create_with_seed(base, "anchor:idl", program_id)


class IdlProgramAccount(TypedDict):
    """The on-chain account of the IDL."""

    authority: solana.publickey.PublicKey
    data: bytes


IDL_ACCOUNT_LAYOUT = CStruct("authority" / _BorshPubkey, "data" / Vec(U8))


def _decode_idl_account(data: bytes) -> IdlProgramAccount:
    """Decode on-chain IDL.

    Args:
        data: binary data from the account that stores the IDL.

    Returns:
        Decoded IDL.
    """
    return IDL_ACCOUNT_LAYOUT.parse(data)
