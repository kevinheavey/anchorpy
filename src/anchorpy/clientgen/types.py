from pathlib import Path
from typing import cast, Union as TypingUnion
from pyheck import snake
from genpy import FromImport, Import, Assign, Suite, ImportAs, Class, Return
from anchorpy.idl import (
    Idl,
    _IdlTypeDefTyStruct,
    _IdlField,
    _IdlEnumVariant,
    _IdlEnumFieldsTuple,
    _IdlEnumFieldsNamed,
)
from anchorpy.clientgen.utils import (
    Union,
    Tuple,
    Method,
    InitMethod,
    StaticMethod,
    ClassMethod,
    TypedParam,
    TypedDict,
    StrDict,
    StrDictEntry,
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
        print("struct or enum file")
        print(code)


def gen_struct(idl: Idl, name: str, fields: list[_IdlField]) -> str:
    imports = Suite(
        [
            Import("typing"),
            FromImport("dataclasses", ["dataclass"]),
            FromImport("construct", "Container"),
            FromImport("solana.publickey", ["PublicKey"]),
            FromImport("..", ["types"]),
            ImportAs("borsh_construct", "borsh"),
        ]
    )
    fields_interface_name = _fields_interface_name(name)
    json_interface_name = _json_interface_name(name)
    fields_interface_params: list[TypedParam] = []
    json_interface_params: list[TypedParam] = []
    layout_items: list[str] = []
    from_decoded_items: list[str] = []
    to_encodable_items: list[str] = []
    to_json_items: list[str] = []
    from_json_items: list[str] = []
    for field in fields:
        fields_interface_params.append(
            TypedParam(field.name, _py_type_from_idl(idl, field.type))
        )
        json_interface_params.append(
            TypedParam(field.name, _idl_type_to_json_type(field.type))
        )
        layout_items.append(_layout_for_type(field.type, field.name))
        from_decoded_items.append(
            f"{field.name}={_field_from_decoded(idl, field, 'obj.')}"
        )
        to_encodable_items.append(
            f'"{field.name}": {_field_to_encodable(idl, field, "fields.")}'
        )
        to_json_items.append(f'"{field.name}": {_field_to_json(idl, field, "self.")}')
        from_json_items.append(f"{field.name}={_field_from_json(field)}")
    fields_interface = TypedDict(fields_interface_name, fields_interface_params)
    json_interface = TypedDict(json_interface_name, json_interface_params)
    layout = f"borsh.CStruct({','.join(layout_items)})"
    args_for_from_decoded = ",".join(from_decoded_items)
    to_encodable_body = "{" + ",".join(to_encodable_items) + "}"
    to_json_body = "{" + ",".join(to_json_items) + "}"
    args_for_from_json = ",".join(from_json_items)
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
                [TypedParam("obj", "Container")],
                Return(f"cls({fields_interface_name}({args_for_from_decoded}))"),
                f'"{name}"',
            ),
            Method(
                "to_encodable", [], Return(to_encodable_body), "dict[str, typing.Any]"
            ),
            Method("to_json", [], Return(to_json_body), json_interface_name),
            ClassMethod(
                "from_json",
                [TypedParam("obj", json_interface_name)],
                Return(f"cls({json_interface_name}({args_for_from_json}))"),
                f'"{name}"',
            ),
        ],
    )
    return str(Suite([imports, fields_interface, json_interface, struct_cls]))


def gen_enum(idl: Idl, name: str, variants: list[_IdlEnumVariant]) -> str:
    imports = Suite(
        [
            Import("typing"),
            FromImport("dataclasses", ["dataclass"]),
            FromImport("construct", "Container"),
            FromImport("solana.publickey", ["PublicKey"]),
            FromImport("..", ["types"]),
            ImportAs("borsh_construct", "borsh"),
        ]
    )
    for idx, variant in enumerate(variants):
        discriminator = idx
        fields = variant.fields
        fields_interface_name = _fields_interface_name(variant.name)
        value_interface_name = _value_interface_name(variant.name)
        json_interface_name = _json_interface_name(variant.name)
        json_interface_value_type_name = f"{json_interface_name}Value"
        fields_type_aliases: list[TypingUnion[TypedDict, Assign]] = []
        value_type_aliases: list[TypingUnion[TypedDict, Assign]] = []
        extra_aliases: list[TypedDict] = []
        encodable_value_items: list[StrDictEntry] = []
        to_json_items_base = StrDictEntry("kind", variant.name)
        json_interface_kind_field = TypedParam("kind", f'"{variant.name}"')
        if fields:
            if isinstance(fields[0], _IdlField):
                named_enum_fields = cast(_IdlEnumFieldsNamed, fields)
                field_type_alias_entries: list[TypedParam] = []
                value_type_alias_entries: list[TypedParam] = []
                json_interface_value_type_entries: list[TypedParam] = []
                init_method_body_items: list[StrDictEntry] = []
                json_value_items: list[StrDictEntry] = []
                for named_field in named_enum_fields:
                    field_type_alias_entries.append(
                        TypedParam(
                            named_field.name, _py_type_from_idl(idl, named_field.type)
                        )
                    )
                    value_type_alias_entries.append(
                        TypedParam(
                            named_field.name,
                            _py_type_from_idl(
                                idl,
                                named_field.type,
                                use_fields_interface_for_struct=False,
                            ),
                        )
                    )
                    json_interface_value_type_entries.append(
                        TypedParam(
                            named_field.name, _idl_type_to_json_type(named_field.type)
                        )
                    )
                    init_method_body_items.append(
                        StrDictEntry(
                            named_field.name,
                            _struct_field_initializer(idl, named_field),
                        )
                    )
                    json_value_items.append(
                        StrDictEntry(
                            named_field.name,
                            _field_to_json(idl, named_field, "self.value."),
                        )
                    )
                    encodable_value_items.append(
                        StrDictEntry(
                            named_field.name,
                            _field_to_encodable(idl, named_field, "self.value."),
                        )
                    )

                fields_type_aliases.append(
                    TypedDict(fields_interface_name, field_type_alias_entries)
                )
                value_type_aliases.append(
                    TypedDict(value_interface_name, value_type_alias_entries)
                )
                json_interface_value_field_type = TypedDict(
                    json_interface_value_type_name, json_interface_value_type_entries
                )
                extra_aliases.append(json_interface_value_field_type)
            else:
                tuple_enum_fields = cast(_IdlEnumFieldsTuple, fields)
                field_type_alias_elements: list[str] = []
                value_type_alias_elements: list[str] = []
                json_interface_value_elements: list[str] = []
                tuple_elements: list[str] = []
                json_value_elements: list[str] = []
                for i, unnamed_field in enumerate(tuple_enum_fields):
                    field_type_alias_elements.append(
                        _py_type_from_idl(idl, unnamed_field)
                    )
                    value_type_alias_elements.append(
                        _py_type_from_idl(
                            idl, unnamed_field, use_fields_interface_for_struct=False
                        )
                    )
                    json_interface_value_elements.append(
                        _idl_type_to_json_type(unnamed_field)
                    )
                    name = f"value[{i}]"
                    tuple_elements.append(
                        _struct_field_initializer(
                            idl, _IdlField(name, unnamed_field), ""
                        )
                    )
                    json_value_elements.append(
                        _field_to_json(idl, _IdlField(name, unnamed_field))
                    )
                    encodable = _field_to_encodable(
                        idl, _IdlField(f"[{i}]", unnamed_field), "self.value"
                    )
                    encodable_value_items.append(StrDictEntry(f"_{i}", encodable))
                fields_type_aliases.append(
                    Assign(
                        fields_interface_name,
                        Tuple(field_type_alias_elements),
                    )
                )
                value_type_aliases.append(
                    Assign(
                        value_interface_name,
                        Tuple(value_type_alias_elements),
                    )
                )
                json_interface_value_field_type = Tuple(json_interface_value_elements)
                init_method_body = Assign(
                    "self.value",
                    init_method_body_items,
                )
                json_value_entry = StrDict(json_value_items)
                to_json_body = Return(
                    StrDict(
                        [to_json_items_base, StrDictEntry("value", json_value_entry)]
                    )
                )
                encodable_value_entry = StrDict(encodable_value_items)
                tuple_str = ",".join(x for x in tuple_elements)
                init_method_body = Assign(
                    "self.value",
                    tuple_str,
                )
                to_json_body = Return(
                    StrDict(
                        [
                            to_json_items_base,
                            StrDictEntry("value", f'[{",".join(json_value_elements)}]'),
                        ]
                    )
                )
            json_interface_params = [
                TypedParam("value", str(json_interface_value_field_type)),
                json_interface_kind_field,
            ]
        else:
            to_json_method = ClassMethod(
                "to_json",
                [],
                Return(StrDict([to_json_items_base])),
                json_interface_name,
            )
            json_interface_params = [json_interface_kind_field]
        json_interface = TypedDict(json_interface_name, json_interface_params)
        class_common_attrs = [
            Assign("discriminator", discriminator),
            Assign("kind", f'"{variant.name}"'),
        ]
        to_encodable_body = Return(
            StrDict([StrDictEntry(variant.name, encodable_value_entry)])
        )
        to_json_method = Method("to_json", [], to_json_body, json_interface_name)
        to_encodable_method = Method("to_encodable", [], to_encodable_body, "dict")
        init_method = InitMethod(
            [TypedParam("value", fields_interface_name)], init_method_body
        )
        attrs = [
            *class_common_attrs,
            init_method,
            to_json_method,
            to_encodable_method,
        ]
        klass = Class(variant.name, None, attrs)
