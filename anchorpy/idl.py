from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Union, Optional

from anchorpy.public_key import PublicKey

IdlType = str


@dataclass
class IdlAccount:
    name: str
    is_mut: bool
    is_signer: bool

    @staticmethod
    def parse_json(j) -> IdlAccount:
        return IdlAccount(name=j["name"], is_mut=j["isMut"], is_signer=j["isSigner"])


@dataclass
class IdlAccounts:
    # Nested/recursive version of IdlAccount
    name: str
    accounts: IdlAccountItem


IdlAccountItem = Union[IdlAccount, IdlAccounts]


@dataclass
class IdlState:
    struct: IdlTypeDef
    methods: List[IdlStateMethod]

    @staticmethod
    def parse_json(j):
        struct = IdlTypeDef.parse_json(j["struct"])
        methods = [IdlStateMethod.parse_json(method) for method in j["methods"]]
        return IdlState(struct=struct, methods=methods)


@dataclass
class IdlInstruction:
    name: str
    accounts: List[IdlAccount]
    args: List[IdlField]

    @staticmethod
    def parse_json(j) -> IdlInstruction:
        name = j["name"]
        accounts = [IdlAccount.parse_json(account) for account in j["accounts"]]
        args = [IdlField.parse_json(arg) for arg in j["args"]]
        return IdlInstruction(name=name, accounts=accounts, args=args)


@dataclass
class IdlEnumVariant:
    name: str
    fields: Union[List[IdlField], List[IdlType]]

    @staticmethod
    def parse_json(j) -> IdlEnumVariant:
        pass
        # return IdlEnumVariant()


@dataclass
class IdlTypeDefTy:
    kind: str
    fields: List[IdlField] = None
    variants: List[IdlEnumVariant] = None

    @staticmethod
    def parse_json(j) -> IdlTypeDefTy:
        return IdlTypeDefTy(kind=j["kind"],
                            fields=[IdlField.parse_json(field) for field in j["fields"]] if "fields" in j else [],
                            variants=[IdlEnumVariant.parse_json(ev) for ev in j["variants"]] if "variants" in j else [])


@dataclass
class IdlTypeDef:
    name: str
    type_of: IdlTypeDefTy

    @staticmethod
    def parse_json(j) -> IdlTypeDef:
        # TODO (LB)
        type_of = IdlTypeDefTy.parse_json(j["type"])
        return IdlTypeDef(j["name"], type_of)


@dataclass
class IdlField:
    name: str
    type_of: IdlType

    @staticmethod
    def parse_json(j) -> IdlField:
        type_of = j["type"]
        return IdlField(name=j["name"], type_of=type_of)


@dataclass
class IdlEventField:
    name: str
    type_of: str
    index: bool

    @staticmethod
    def parse_json(j) -> IdlEventField:
        return IdlEventField(name=j["name"], type_of=j["type"], index=j["index"])


@dataclass
class IdlEvent:
    name: str
    fields: List[IdlEventField]

    @staticmethod
    def parse_json(j) -> IdlEvent:
        return IdlEvent(name=j["name"], fields=[IdlEventField.parse_json(field) for field in j["fields"]])


@dataclass
class IdlErrorCode:
    code: int
    name: str
    msg: str = ""

    @staticmethod
    def parse_json(j) -> IdlErrorCode:
        return IdlErrorCode(code=j["code"], name=j["name"], msg=j["msg"] if "msg" in j else "")


IdlStateMethod = IdlInstruction


@dataclass
class Metadata:
    address: PublicKey

    @staticmethod
    def parse_json(j) -> Metadata:
        return Metadata(address=PublicKey(j["address"]))


@dataclass
class Idl(object):
    version: str
    name: str
    instructions: List[IdlInstruction]
    state: IdlState = None
    accounts: List[IdlTypeDef] = field(default_factory=list)
    types: List[IdlTypeDef] = field(default_factory=list)
    events: List[IdlEvent] = field(default_factory=list)
    errors: List[IdlErrorCode] = field(default_factory=list)
    metadata: Optional[Metadata] = None

    @staticmethod
    def parse_json(j) -> Idl:
        instructions = list()
        accounts = list()
        types = list()
        events = list()
        errors = list()
        state = None
        metadata = None

        for instruction in j["instructions"]:
            instructions.append(IdlInstruction.parse_json(instruction))

        if "state" in j:
            state = IdlState.parse_json(j["state"])

        if "accounts" in j:
            accounts = [IdlTypeDef.parse_json(account) for account in j["accounts"]]

        if "types" in j:
            types = [IdlTypeDef.parse_json(t) for t in j["types"]]

        if "events" in j:
            events = [IdlEvent.parse_json(event) for event in j["events"]]

        if "errors" in j:
            errors = [IdlErrorCode.parse_json(error) for error in j["errors"]]

        if "metadata" in j:
            metadata = Metadata.parse_json(j["metadata"])

        return Idl(version=j["version"],
                   name=j["name"],
                   instructions=instructions,
                   state=state,
                   accounts=accounts,
                   types=types,
                   events=events,
                   errors=errors,
                   metadata=metadata)
