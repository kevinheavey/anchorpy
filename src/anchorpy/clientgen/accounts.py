from pathlib import Path
from typing import cast, Union as TypingUnion
from dataclasses import dataclass
from pyheck import snake
from genpy import (
    FromImport,
    Import,
    Assign,
    Suite,
    ImportAs,
    Return,
    For,
    If,
    IfThen,
    Raise,
    Generable,
    Statement,
)
from anchorpy.coder.accounts import _account_discriminator
from anchorpy.idl import (
    Idl,
    _IdlTypeDefTyStruct,
    _IdlField,
    _IdlType,
    _IdlEnumVariant,
    _IdlEnumFieldsTuple,
    _IdlEnumFieldsNamed,
    _IdlTypeDef,
    _IdlAccountDef,
)
from anchorpy.clientgen.utils import (
    Union,
    Class,
    Tuple,
    List,
    Method,
    InitMethod,
    StaticMethod,
    ClassMethod,
    TypedParam,
    TypedDict,
    StrDict,
    StrDictEntry,
    Function,
)
from anchorpy.clientgen.common import (
    _fields_interface_name,
    _json_interface_name,
    _kind_interface_name,
    _value_interface_name,
    _py_type_from_idl,
    _idl_type_to_json_type,
    _struct_field_initializer,
    _layout_for_type,
    _field_from_decoded,
    _field_to_encodable,
    _field_to_json,
    _field_from_json,
)


def gen_accounts(idl: Idl, out: Path) -> None:
    accounts = idl.accounts
    if accounts is None or not accounts:
        return
    gen_index_file(idl, out)
    gen_account_files(idl, out)


def gen_index_file(idl: Idl, out: Path) -> None:
    code = gen_index_code(idl)


def gen_index_code(idl: Idl) -> str:
    imports: list[FromImport] = []
    for acc in idl.accounts:
        members = [
            acc.name,
            _fields_interface_name(acc.name),
            _json_interface_name(acc.name),
        ]
        imports.append(FromImport(f".{snake(acc.name)}", members))
    return str(Suite(imports))


def gen_account_files(idl: Idl, out: Path) -> None:
    for acc in idl.accounts:
        filename = f"{snake(acc.name)}.py"
        path = out / filename
        code = gen_account_code(acc, idl)


def gen_account_code(acc: _IdlAccountDef, idl: Idl) -> str:
    base_imports = [
        FromImport("typing", ["Optional"]),
        FromImport(
            "solana.publickey",
            ["PublicKey"],
            FromImport("solana.rpc.api.async_client", ["AsyncClient"]),
            FromImport("solana.rpc.commitment", ["Commitment"]),
            ImportAs("borsh_construct", "borsh"),
            FromImport("..program_id", ["PROGRAM_ID"]),
        ),
    ]
    imports = [*base_imports, FromImport(".", ["types"])] if idl.types else base_imports
    fields_interface_params: list[TypedParam] = []
    json_interface_params: list[TypedParam] = []
    fields = acc.type.fields
    name = acc.name
    fields_interface_name = _fields_interface_name(name)
    json_interface_name = _json_interface_name(name)
    layout_items: list[str] = []
    init_body_assignments: list[Assign] = []
    for field in fields:
        fields_interface_params.append(
            TypedParam(field.name, _py_type_from_idl(idl, field.type))
        )
        json_interface_params.append(
            TypedParam(field.name, _idl_type_to_json_type(field.type))
        )
        layout_items.append(_layout_for_type(field.type, field.name))
        initializer = _struct_field_initializer(idl, field)
        init_body_assignments.append(Assign(f"self.{field.name}", initializer))
    fields_interface = TypedDict(fields_interface_name, fields_interface_params)
    json_interface = TypedDict(json_interface_name, json_interface_params)
    discriminator_assignment = Assign("discriminator", _account_discriminator(name))
    layout_assignment = Assign("layout", f"borsh.CStruct({','.join(layout_items)})")
    init_method = InitMethod(
        [TypedParam("fields", fields_interface_name)], Suite(init_body_assignments)
    )
    fetch_method = ClassMethod(
        "fetch",
        [
            TypedParam("conn", "AsyncClient"),
            TypedParam("address", "PublicKey"),
            TypedParam("commitment", "Optional[Commitment] = None"),
        ],
        Suite(
            [
                Assign(
                    "resp",
                    "await conn.get_account_info(address, commitment=commitment)",
                ),
                Assign("info", 'resp["result"]["value"]'),
                IfThen('info is None"', Return("None")),
                IfThen(
                    'info["owner"] != str(PROGRAM_ID)',
                    Raise('ValueError("Account does not belong to this program")'),
                ),
                Return('cls.decode(info["data"])'),
            ]
        ),
        f"typing.Optional[{name}]",
        is_async=True,
    )
    fetch_multiple_method = ClassMethod(
        "fetch_multiple",
        [
            TypedParam("conn", "AsyncClient"),
            TypedParam("addresses", "list[PublicKey]"),
            TypedParam("commitment", "Optional[Commitment] = None"),
        ],
        Suite(
            [
                Assign(
                    "resp",
                    "await conn.get_account_info(address, commitment=commitment)",
                ),
                Assign("infos", 'resp["result"]["value"]'),
                Assign("result", "[]"),
                For(
                    "info",
                    "infos",
                    Suite(
                        [
                            IfThen('info is None"', Return("None")),
                            IfThen(
                                'info["owner"] != str(PROGRAM_ID)',
                                Raise(
                                    'ValueError("Account does not belong to this program")'
                                ),
                            ),
                            Statement('res.append(cls.decode(info["data"]))'),
                        ]
                    ),
                ),
                Return("res"),
            ]
        ),
        f"list[Optional[{name}]]",
    )
