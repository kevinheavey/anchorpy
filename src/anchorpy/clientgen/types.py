from pathlib import Path
from pyheck import snake
from genpy import FromImport, Assign, Suite
from anchorpy.idl import Idl, _IdlTypeDefTyStruct, _IdlTypeDefTyEnum
from anchorpy.clientgen.utils import Union
from anchorpy.clientgen.common import _fields_interface_name, _json_interface_name


def gen_types(idl: Idl, out: Path) -> None:
    types = idl.types
    if types is None or not types:
        return
    gen_index_file(idl, out)
    gen_type_files(idl, out)


def gen_index_file(idl: Idl, out: Path) -> None:
    code = gen_index_code(idl)
    print("types index file")
    print(code)


def gen_index_code(idl: Idl) -> str:
    lines = []
    for ty in idl.types:
        ty_type = ty.type
        module_name = snake(ty.name)
        if isinstance(ty_type, _IdlTypeDefTyStruct):
            code_to_add = FromImport(
                f".{module_name}",
                [
                    ty.name,
                    _fields_interface_name(ty.name),
                    _json_interface_name(ty.name),
                ],
            )
        else:
            import_line = FromImport(".", [module_name])
            json_variants = Union(
                [
                    f"{ty.name}.{_json_interface_name(variant.name)}"
                    for variant in ty_type.variants
                ]
            )
            json_type_alias = Assign(_json_interface_name(ty.name), json_variants)
            code_to_add = Suite([import_line, json_type_alias])
        lines.append(code_to_add)
    return str(Suite(lines))
