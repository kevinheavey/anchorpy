from typing import get_args, cast, Optional
from pathlib import Path
from pyheck import snake, upper_camel
from genpy import (
    FromImport,
    Assign,
    Suite,
    ImportAs,
    Return,
    For,
    If,
    Raise,
    Statement,
)
from anchorpy.coder.accounts import _account_discriminator
from anchorpy.idl import (
    Idl,
    _IdlAccountDef,
    _IdlAccounts,
    _IdlAccountItem,
)
from anchorpy.clientgen.utils import (
    Class,
    Method,
    InitMethod,
    ClassMethod,
    TypedParam,
    TypedDict,
    StrDict,
    StrDictEntry,
)
from anchorpy.clientgen.common import (
    _fields_interface_name,
    _json_interface_name,
    _py_type_from_idl,
    _idl_type_to_json_type,
    _struct_field_initializer,
    _layout_for_type,
    _field_from_decoded,
    _field_to_json,
    _field_from_json,
)


def args_interface_name(ix_name: str) -> str:
    return f"{upper_camel(ix_name)}Args"


def accounts_interface_name(ix_name: str) -> str:
    return f"{upper_camel(ix_name)}Accounts"


def gen_accounts(
    name,
    idl_accs: list[_IdlAccountItem],
    extra_typeddicts: Optional[list[TypedDict]] = None,
) -> list[TypedDict]:
    extra_typeddicts_to_use = [] if extra_typeddicts is None else extra_typeddicts
    params: list[TypedParam] = []
    for acc in idl_accs:
        if isinstance(acc, _IdlAccounts):
            nested_accs = cast(_IdlAccounts, acc)
            nested_acc_name = f"{upper_camel(nested_accs.name)}Nested"
            params.append(TypedParam(acc.name, nested_acc_name))
            extra_typeddicts_to_use = extra_typeddicts_to_use + (
                gen_accounts(
                    nested_acc_name,
                    nested_accs.accounts,
                    extra_typeddicts_to_use,
                )
            )
        else:
            params.append(TypedParam(acc.name, "PublicKey"))
    return [TypedDict(name, params)] + extra_typeddicts_to_use


def gen_instruction_files(idl: Idl, out: Path) -> None:
    for ix in idl.instructions:
        filename = (out / ix.name).with_suffix(".py")
        types_import = [FromImport("..", ["types"])] if idl.types else []
        imports = [
            FromImport("solana.publickey", ["PublicKey"]),
            FromImport("solana.transaction", ["TransactionInstruction"]),
            ImportAs("borsh_construct", "borsh"),
            *types_import,
            FromImport("..", ["PROGRAM_ID"]),
        ]
        args_interface_params: list[TypedParam] = []
        layout_items: list[str] = []
        for arg in ix.args:
            args_interface_params.append(
                TypedParam(arg.name, _py_type_from_idl(idl, arg.type))
            )
            layout_items.append(_layout_for_type(arg.type, arg.name))
        if ix.args:
            args_interface_container = [
                TypedDict(args_interface_name(ix.name), args_interface_params)
            ]
            layout_assignment_container = [
                Assign("layout", f"borsh.CStruct({','.join(layout_items)})")
            ]
        else:
            args_interface_container = []
            layout_assignment_container = []
