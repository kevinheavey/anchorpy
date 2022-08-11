from typing import cast, Optional
from black import format_str, FileMode
from autoflake import fix_code
from pathlib import Path
from pyheck import upper_camel
from genpy import (
    Import,
    FromImport,
    Assign,
    Suite,
    Collection,
    ImportAs,
    Return, If, Line,
)
from anchorpy.coder.common import _sighash
from anchorpy.idl import (
    Idl,
    _IdlAccounts,
    _IdlAccountItem,
)
from anchorpy.clientgen.genpy_extension import (
    TypedParam,
    TypedDict,
    StrDict,
    StrDictEntry,
    List,
    Function,
    ANNOTATIONS_IMPORT,
)
from anchorpy.clientgen.common import (
    _py_type_from_idl,
    _layout_for_type,
    _field_to_encodable,
    _sanitize
)


def gen_instructions(idl: Idl, root: Path) -> None:
    instructions_dir = root / "instructions"
    instructions_dir.mkdir(exist_ok=True)
    gen_index_file(idl, instructions_dir)
    instructions = gen_instructions_code(idl, instructions_dir)
    for path, code in instructions.items():
        formatted = format_str(code, mode=FileMode())
        fixed = fix_code(formatted, remove_all_unused_imports=True)
        path.write_text(fixed)


def gen_index_file(idl: Idl, instructions_dir: Path) -> None:
    code = gen_index_code(idl)
    path = instructions_dir / "__init__.py"
    formatted = format_str(code, mode=FileMode())
    path.write_text(formatted)


def gen_index_code(idl: Idl) -> str:
    imports: list[FromImport] = []
    for ix in idl.instructions:
        ix_name = _sanitize(ix.name)
        import_members: list[str] = [ix_name]
        if ix.args:
            import_members.append(_args_interface_name(ix.name))
        if ix.accounts:
            import_members.append(_accounts_interface_name(ix.name))
        if import_members:
            imports.append(FromImport(f".{ix_name}", import_members))
    return str(Collection(imports))


def _args_interface_name(ix_name: str) -> str:
    return f"{upper_camel(ix_name)}Args"


def _accounts_interface_name(ix_name: str) -> str:
    return f"{upper_camel(ix_name)}Accounts"


def recurse_accounts(accs: list[_IdlAccountItem], nested_names: list[str]) -> list[str]:
    elements: list[str] = []
    for acc in accs:
        names = [*nested_names, _sanitize(acc.name)]
        if isinstance(acc, _IdlAccounts):
            nested_accs = cast(_IdlAccounts, acc)
            elements.extend(recurse_accounts(nested_accs.accounts, names))
        else:
            nested_keys = [f'["{key}"]' for key in names]
            dict_accessor = "".join(nested_keys)
            elements.append(
                f"AccountMeta(pubkey=accounts{dict_accessor}, "
                f"is_signer={acc.is_signer}, "
                f"is_writable={acc.is_mut})"
            )
    return elements


def gen_accounts(
    name,
    idl_accs: list[_IdlAccountItem],
    extra_typeddicts: Optional[list[TypedDict]] = None
) -> list[TypedDict]:
    extra_typeddicts_to_use = [] if extra_typeddicts is None else extra_typeddicts
    params: list[TypedParam] = []
    for acc in idl_accs:
        acc_name = _sanitize(acc.name)
        if isinstance(acc, _IdlAccounts):
            nested_accs = cast(_IdlAccounts, acc)
            nested_acc_name = f"{upper_camel(nested_accs.name)}Nested"
            params.append(TypedParam(acc_name, f"{nested_acc_name}"))
            extra_typeddicts_to_use = extra_typeddicts_to_use + (
                gen_accounts(
                    nested_acc_name,
                    nested_accs.accounts,
                    extra_typeddicts_to_use,
                )
            )
        else:
            params.append(TypedParam(acc_name, "PublicKey"))
    maybe_typed_dict_container = [TypedDict(name, params)] if params else []
    return maybe_typed_dict_container + extra_typeddicts_to_use


def gen_instructions_code(idl: Idl, out: Path) -> dict[Path, str]:
    types_import = [FromImport("..", ["types"])] if idl.types else []
    imports = [
        ANNOTATIONS_IMPORT,
        Import("typing"),
        FromImport("solana.publickey", ["PublicKey"]),
        FromImport("solana.transaction", ["TransactionInstruction", "AccountMeta"]),
        FromImport("anchorpy.borsh_extension", ["EnumForCodegen", "BorshPubkey"]),
        FromImport("construct", ["Pass", "Construct"]),
        ImportAs("borsh_construct", "borsh"),
        *types_import,
        FromImport("..program_id", ["PROGRAM_ID"]),
    ]
    result = {}
    for ix in idl.instructions:
        ix_name = _sanitize(ix.name)
        filename = (out / ix_name).with_suffix(".py")
        args_interface_params: list[TypedParam] = []
        layout_items: list[str] = []
        encoded_args_entries: list[StrDictEntry] = []
        accounts_interface_name = _accounts_interface_name(ix.name)
        for arg in ix.args:
            arg_name = _sanitize(arg.name)
            args_interface_params.append(
                TypedParam(
                    arg_name,
                    _py_type_from_idl(
                        idl=idl,
                        ty=arg.type,
                        types_relative_imports=False,
                        use_fields_interface_for_struct=False,
                    ),
                )
            )
            layout_items.append(
                _layout_for_type(
                    idl=idl, ty=arg.type, name=arg_name, types_relative_imports=False
                )
            )
            encoded_args_entries.append(
                StrDictEntry(
                    arg_name,
                    _field_to_encodable(
                        idl=idl,
                        ty=arg,
                        types_relative_imports=False,
                        val_prefix='args["',
                        val_suffix='"]',
                    ),
                )
            )
        if ix.args:
            args_interface_name = _args_interface_name(ix_name)
            args_interface_container = [
                TypedDict(args_interface_name, args_interface_params)
            ]
            layout_val = f"borsh.CStruct({','.join(layout_items)})"
            layout_assignment_container = [Assign("layout", layout_val)]
            args_container = [TypedParam("args", args_interface_name)]
            encoded_args_val = f"layout.build({StrDict(encoded_args_entries)})"
        else:
            args_interface_container = []
            layout_val = "Pass"
            args_container = []
            layout_assignment_container = []
            encoded_args_val = 'b""'
        accounts_container = (
            [TypedParam("accounts", accounts_interface_name)] if ix.accounts else []
        )
        accounts = gen_accounts(accounts_interface_name, ix.accounts)
        keys_assignment = Assign(
            "keys: list[AccountMeta]",
            f"{List(recurse_accounts(ix.accounts, []))}"
        )
        remaining_accounts_concatenation = If(
            "remaining_accounts is not None",
            Line("keys += remaining_accounts")
        )
        identifier_assignment = Assign("identifier", _sighash(ix.name))
        encoded_args_assignment = Assign("encoded_args", encoded_args_val)
        data_assignment = Assign("data", "identifier + encoded_args")
        returning = Return("TransactionInstruction(keys, program_id, data)")
        ix_fn = Function(
            ix_name,
            [
                *args_container,
                *accounts_container,
                TypedParam("program_id", "PublicKey = PROGRAM_ID"),
                TypedParam(
                    "remaining_accounts",
                    "typing.Optional[typing.List[AccountMeta]] = None"
                ),
            ],
            Suite(
                [
                    keys_assignment,
                    remaining_accounts_concatenation,
                    identifier_assignment,
                    encoded_args_assignment,
                    data_assignment,
                    returning,
                ]
            ),
            "TransactionInstruction",
        )
        contents = Collection(
            [
                *imports,
                *args_interface_container,
                *layout_assignment_container,
                *accounts,
                ix_fn,
            ]
        )
        result[filename] = str(contents)
    return result
