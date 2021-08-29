from dataclasses import dataclass, field
from typing import List, Union, Optional, Dict, Any

from typedload import datadumper, dataloader
from solana.publickey import PublicKey

dumper = datadumper.Dumper()
loader = dataloader.Loader()
dumper.strconstructed.add(PublicKey)
loader.strconstructed.add(PublicKey)  # type: ignore

IdlType = Union[
    bool,
    int,
    bytes,
    str,
    PublicKey,
    "IdlTypeVec",
    "IdlTypeOption",
    "IdlTypeDefined",
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
    name: str
    type_of: IdlType = field(metadata={"name": "type"})


@dataclass
class IdlAccount:
    name: str
    is_mut: bool = field(metadata={"name": "isMut"})
    is_signer: bool = field(metadata={"name": "isSigner"})


@dataclass
class IdlAccounts:
    # Nested/recursive version of IdlAccount
    name: str
    accounts: List["IdlAccountItem"]


@dataclass
class IdlAccounts0:
    name: str
    accounts: List[IdlAccount]


@dataclass
class IdlAccounts1:
    name: str
    accounts: List[Union[IdlAccount, IdlAccounts0]]


IdlAccountItem = Union[IdlAccount, IdlAccounts]
IdlAccountItem1 = Union[IdlAccounts1, IdlAccounts0, IdlAccount]


@dataclass
class IdlState:
    struct: "IdlTypeDef"
    methods: List["IdlStateMethod"]


@dataclass
class IdlInstruction:
    name: str
    accounts: List[IdlAccountItem1]
    args: List[IdlField]


@dataclass
class IdlEnumVariant:
    name: str
    fields: Union[List[IdlField], List[IdlType]]


@dataclass
class IdlTypeDefTy:
    kind: str
    fields: Optional[List[IdlField]] = None
    variants: Optional[List[IdlEnumVariant]] = None


@dataclass
class IdlTypeDef:
    name: str
    type_of: IdlTypeDefTy = field(metadata={"name": "type"})


@dataclass
class IdlEventField:
    name: str
    type_of: str = field(metadata={"name": "type"})
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


IdlStateMethod = IdlInstruction


@dataclass
class Metadata:
    address: PublicKey


@dataclass
class Idl:
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
        return loader.load(idl, cls)
