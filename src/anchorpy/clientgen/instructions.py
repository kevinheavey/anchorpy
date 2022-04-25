from pathlib import Path
from pyheck import snake
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
    _args_interface_name,
)


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
                TypedDict(_args_interface_name(ix.name), args_interface_params)
            ]
            layout_assignment_container = [
                Assign("layout", f"borsh.CStruct({','.join(layout_items)})")
            ]
        else:
            args_interface_container = []
            layout_assignment_container = []
