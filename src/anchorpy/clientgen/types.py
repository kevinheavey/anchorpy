from pathlib import Path
from pyheck import snake
from genpy import FromImport, Import, Assign, Suite, ImportAs, Class, Return
from anchorpy.idl import Idl, _IdlTypeDefTyStruct, _IdlTypeDefTyEnum, _IdlField
from anchorpy.clientgen.utils import (
    Union,
    Dataclass,
    TypedParam,
    Function,
    Method,
    InitMethod,
    StaticMethod,
    ClassMethod,
    TypedParam,
)
from anchorpy.clientgen.common import (
    _fields_interface_name,
    _json_interface_name,
    _kind_interface_name,
    _py_type_from_idl,
    _idl_type_to_json_type,
    _struct_field_initializer,
    _layout_for_type,
    _field_from_decoded,
)


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
                    f"{module_name}.{_json_interface_name(variant.name)}"
                    for variant in ty_type.variants
                ]
            )
            type_variants = Union(
                [
                    f"{module_name}.{_kind_interface_name(variant.name)}"
                    for variant in ty_type.variants
                ]
            )
            kind_type_alias = Assign(_kind_interface_name(ty.name), type_variants)
            json_type_alias = Assign(_json_interface_name(ty.name), json_variants)
            code_to_add = Suite([import_line, kind_type_alias, json_type_alias])
        lines.append(code_to_add)
    return str(Suite(lines))


def gen_type_files(idl: Idl, out: Path) -> None:
    for ty in idl.types:
        code = (
            gen_struct(idl, ty.name, ty.type.fields)
            if isinstance(ty.type, _IdlTypeDefTyStruct)
            else gen_enum(idl, ty.name, ty.type.variants)
        )


def gen_struct(idl: Idl, name: str, fields: list[_IdlField]) -> str:
    imports = Suite(
        [
            Import("typing"),
            FromImport("dataclasses", ["dataclass"]),
            FromImport("solana.publickey", ["PublicKey"]),
            FromImport("..", ["types"]),
            ImportAs("borsh_construct", "borsh"),
        ]
    )
    fields_interface_name = _fields_interface_name(name)
    fields_interface = Dataclass(
        fields_interface_name,
        [
            TypedParam(field.name, _py_type_from_idl(idl, field.type))
            for field in fields
        ],
    )
    json_interface = Dataclass(
        _json_interface_name(name),
        [
            TypedParam(field.name, _idl_type_to_json_type(field.type))
            for field in fields
        ],
    )
    layout_items = tuple(_layout_for_type(field.type, field.name) for field in fields)
    layout = f"borsh.CStruct{layout_items}"
    args_for_from_decoded = ",".join(
        [f"{field.name}={_field_from_decoded(idl, field, 'obj.')}" for field in fields]
    )
    struct_cls = Class(
        name,
        None,
        [
            InitMethod(
                [TypedParam("fields", fields_interface_name)],
                Suite(
                    [
                        Assign(
                            f"self.{field.name}", _struct_field_initializer(idl, field)
                        )
                        for field in fields
                    ]
                ),
            ),
            StaticMethod("layout", [], Return(layout), "borsh.CStruct"),
            ClassMethod(
                "from_decoded",
                [TypedParam("obj", "typing.Any")],
                Return(f"cls({fields_interface_name}({args_for_from_decoded}))"),
                f'"{name}"',
            ),
        ],
    )
