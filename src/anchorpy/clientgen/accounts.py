from pathlib import Path
from typing import cast

from anchorpy_core.idl import (
    Idl,
    IdlField,
    IdlTypeDefinition,
    IdlTypeDefinitionTyStruct,
)
from autoflake import fix_code
from black import FileMode, format_str
from genpy import (
    Assign,
    Collection,
    For,
    FromImport,
    If,
    Import,
    ImportAs,
    Raise,
    Return,
    Statement,
    Suite,
)
from pyheck import snake

from anchorpy.clientgen.common import (
    _field_from_decoded,
    _field_from_json,
    _field_to_json,
    _idl_type_to_json_type,
    _json_interface_name,
    _layout_for_type,
    _py_type_from_idl,
    _sanitize,
)
from anchorpy.clientgen.genpy_extension import (
    Call,
    ClassMethod,
    Continue,
    Dataclass,
    Method,
    NamedArg,
    StrDict,
    StrDictEntry,
    TypedDict,
    TypedParam,
)
from anchorpy.coder.accounts import _account_discriminator


def gen_accounts(idl: Idl, root: Path) -> None:
    accounts = idl.accounts
    if accounts is None or not accounts:
        return
    accounts_dir = root / "accounts"
    accounts_dir.mkdir(exist_ok=True)
    gen_index_file(idl, accounts_dir)
    accounts_dict = gen_accounts_code(idl, accounts_dir)
    for path, code in accounts_dict.items():
        formatted = format_str(code, mode=FileMode())
        fixed = fix_code(formatted, remove_all_unused_imports=True)
        path.write_text(fixed)


def gen_index_file(idl: Idl, accounts_dir: Path) -> None:
    code = gen_index_code(idl)
    formatted = format_str(code, mode=FileMode())
    (accounts_dir / "__init__.py").write_text(formatted)


def gen_index_code(idl: Idl) -> str:
    imports: list[FromImport] = []
    for acc in idl.accounts:
        acc_name = _sanitize(acc.name)
        members = [
            acc_name,
            _json_interface_name(acc_name),
        ]
        module_name = _sanitize(snake(acc.name))
        imports.append(FromImport(f".{module_name}", members))
    return str(Collection(imports))


def gen_accounts_code(idl: Idl, accounts_dir: Path) -> dict[Path, str]:
    res = {}
    for acc in idl.accounts:
        filename = f"{_sanitize(snake(acc.name))}.py"
        path = accounts_dir / filename
        code = gen_account_code(acc, idl)
        res[path] = code
    return res


def gen_account_code(acc: IdlTypeDefinition, idl: Idl) -> str:
    base_imports = [
        Import("typing"),
        FromImport("dataclasses", ["dataclass"]),
        FromImport("construct", ["Construct"]),
        FromImport("solders.pubkey", ["Pubkey"]),
        FromImport("solana.rpc.async_api", ["AsyncClient"]),
        FromImport("solana.rpc.commitment", ["Commitment"]),
        ImportAs("borsh_construct", "borsh"),
        FromImport("anchorpy.coder.accounts", ["ACCOUNT_DISCRIMINATOR_SIZE"]),
        FromImport("anchorpy.error", ["AccountInvalidDiscriminator"]),
        FromImport("anchorpy.utils.rpc", ["get_multiple_accounts"]),
        FromImport(
            "anchorpy.borsh_extension", ["BorshPubkey", "EnumForCodegen", "COption"]
        ),
        FromImport("..program_id", ["PROGRAM_ID"]),
    ]
    imports = (
        [*base_imports, FromImport("..", ["types"])] if idl.types else base_imports
    )
    fields_interface_params: list[TypedParam] = []
    json_interface_params: list[TypedParam] = []
    ty = cast(IdlTypeDefinitionTyStruct, acc.ty)
    fields = ty.fields
    name = _sanitize(acc.name)
    json_interface_name = _json_interface_name(name)
    layout_items: list[str] = []
    init_body_assignments: list[Assign] = []
    decode_body_entries: list[NamedArg] = []
    to_json_entries: list[StrDictEntry] = []
    from_json_entries: list[NamedArg] = []
    for field in fields:
        field_name = _sanitize(snake(field.name))
        fields_interface_params.append(
            TypedParam(
                field_name,
                _py_type_from_idl(
                    idl=idl,
                    ty=field.ty,
                    types_relative_imports=False,
                    use_fields_interface_for_struct=False,
                ),
            )
        )
        json_interface_params.append(
            TypedParam(
                field_name,
                _idl_type_to_json_type(ty=field.ty, types_relative_imports=False),
            )
        )
        layout_items.append(
            _layout_for_type(
                idl=idl, ty=field.ty, name=field_name, types_relative_imports=False
            )
        )
        init_body_assignments.append(
            Assign(f"self.{field_name}", f'fields["{field_name}"]')
        )
        decode_body_entries.append(
            NamedArg(
                field_name,
                _field_from_decoded(
                    idl=idl,
                    ty=IdlField(name=snake(field.name), docs=None, ty=field.ty),
                    types_relative_imports=False,
                    val_prefix="dec.",
                ),
            )
        )
        to_json_entries.append(
            StrDictEntry(field_name, _field_to_json(idl, field, "self."))
        )
        from_json_entries.append(
            NamedArg(
                field_name,
                _field_from_json(idl=idl, ty=field, types_relative_imports=False),
            )
        )
    json_interface = TypedDict(json_interface_name, json_interface_params)
    discriminator_assignment = Assign(
        "discriminator: typing.ClassVar", _account_discriminator(name)
    )
    layout_assignment = Assign(
        "layout: typing.ClassVar", f"borsh.CStruct({','.join(layout_items)})"
    )
    fetch_method = ClassMethod(
        "fetch",
        [
            TypedParam("conn", "AsyncClient"),
            TypedParam("address", "Pubkey"),
            TypedParam("commitment", "typing.Optional[Commitment] = None"),
            TypedParam("program_id", "Pubkey = PROGRAM_ID"),
        ],
        Suite(
            [
                Assign(
                    "resp",
                    "await conn.get_account_info(address, commitment=commitment)",
                ),
                Assign("info", "resp.value"),
                If("info is None", Return("None")),
                If(
                    "info.owner != program_id",
                    Raise('ValueError("Account does not belong to this program")'),
                ),
                Assign("bytes_data", "info.data"),
                Return("cls.decode(bytes_data)"),
            ]
        ),
        f'typing.Optional["{name}"]',
        is_async=True,
    )
    account_does_not_belong_raise = Raise(
        'ValueError("Account does not belong to this program")'
    )
    fetch_multiple_return_type = f'typing.List[typing.Optional["{name}"]]'
    fetch_multiple_method = ClassMethod(
        "fetch_multiple",
        [
            TypedParam("conn", "AsyncClient"),
            TypedParam("addresses", "list[Pubkey]"),
            TypedParam("commitment", "typing.Optional[Commitment] = None"),
            TypedParam("program_id", "Pubkey = PROGRAM_ID"),
        ],
        Suite(
            [
                Assign(
                    "infos",
                    (
                        "await get_multiple_accounts"
                        "(conn, addresses,commitment=commitment)"
                    ),
                ),
                Assign(f"res: {fetch_multiple_return_type}", "[]"),
                For(
                    "info",
                    "infos",
                    Suite(
                        [
                            If(
                                "info is None",
                                Suite([Statement("res.append(None)"), Continue()]),
                            ),
                            If(
                                "info.account.owner != program_id",
                                account_does_not_belong_raise,
                            ),
                            Statement("res.append(cls.decode(info.account.data))"),
                        ]
                    ),
                ),
                Return("res"),
            ]
        ),
        f'typing.List[typing.Optional["{name}"]]',
        is_async=True,
    )
    decode_body_end = Call("cls", decode_body_entries)
    account_invalid_raise = Raise(
        'AccountInvalidDiscriminator("The discriminator for this account is invalid")'
    )
    decode_method = ClassMethod(
        "decode",
        [TypedParam("data", "bytes")],
        Suite(
            [
                If(
                    "data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator",
                    account_invalid_raise,
                ),
                Assign(
                    "dec", f"{name}.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])"
                ),
                Return(decode_body_end),
            ]
        ),
        f'"{name}"',
    )
    to_json_body = StrDict(to_json_entries)
    to_json_method = Method("to_json", [], Return(to_json_body), json_interface_name)
    from_json_body = Call("cls", from_json_entries)
    from_json_method = ClassMethod(
        "from_json",
        [TypedParam("obj", json_interface_name)],
        Return(from_json_body),
        f'"{name}"',
    )
    klass = Dataclass(
        name,
        [
            discriminator_assignment,
            layout_assignment,
            *fields_interface_params,
            fetch_method,
            fetch_multiple_method,
            decode_method,
            to_json_method,
            from_json_method,
        ],
    )
    return str(
        Collection(
            [
                *imports,
                json_interface,
                klass,
            ]
        )
    )
