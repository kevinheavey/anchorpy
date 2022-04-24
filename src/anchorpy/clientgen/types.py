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
    If,
    Raise,
    Generable,
)
from anchorpy.idl import (
    Idl,
    _IdlTypeDefTyStruct,
    _IdlField,
    _IdlType,
    _IdlEnumVariant,
    _IdlEnumFieldsTuple,
    _IdlEnumFieldsNamed,
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
            FromImport("construct", ["Container"]),
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


def _make_cstruct(fields: dict[str, str]) -> str:
    formatted_fields = ",".join([f'"{key}" / {val}' for key, val in fields.items()])
    return f"borsh.CStruct({formatted_fields})"


@dataclass
class _NamedFieldRecord:
    field_type_alias_entry: TypedParam
    value_type_alias_entry: TypedParam
    json_interface_value_type_entry: TypedParam
    init_method_body_item: StrDictEntry
    json_value_item: StrDictEntry
    encodable_value_item: StrDictEntry
    init_entry_for_from_decoded: StrDictEntry
    init_entry_for_from_json: StrDictEntry


def _make_named_field_record(named_field: _IdlField, idl: Idl) -> _NamedFieldRecord:
    return _NamedFieldRecord(
        field_type_alias_entry=TypedParam(
            named_field.name, _py_type_from_idl(idl, named_field.type)
        ),
        value_type_alias_entry=TypedParam(
            named_field.name,
            _py_type_from_idl(
                idl,
                named_field.type,
                use_fields_interface_for_struct=False,
            ),
        ),
        json_interface_value_type_entry=TypedParam(
            named_field.name, _idl_type_to_json_type(named_field.type)
        ),
        init_method_body_item=StrDictEntry(
            named_field.name,
            _struct_field_initializer(idl, named_field),
        ),
        json_value_item=StrDictEntry(
            named_field.name,
            _field_to_json(idl, named_field, 'self.value["', '"]'),
        ),
        encodable_value_item=StrDictEntry(
            named_field.name,
            _field_to_encodable(idl, named_field, 'self.value["', '"]'),
        ),
        init_entry_for_from_decoded=StrDictEntry(
            named_field.name,
            _field_from_decoded(
                idl,
                _IdlField(f'val["{named_field.name}"]', named_field.type),
                "",
            ),
        ),
        init_entry_for_from_json=StrDictEntry(
            named_field.name,
            _field_from_json(
                named_field,
                'obj["value"]',
            ),
        ),
    )


@dataclass
class _UnnamedFieldRecord:
    field_type_alias_element: str
    value_type_alias_element: str
    json_interface_value_element: str
    tuple_element: str
    json_value_element: str
    encodable_value_item: StrDict
    init_element_for_from_decoded: str
    init_element_for_from_json: str


def _make_unnamed_field_record(
    index: int,
    unnamed_field: _IdlType,
    idl: Idl,
) -> _UnnamedFieldRecord:
    elem_name = f"value[{index}]"
    encodable = _field_to_encodable(
        idl, _IdlField(f"[{index}]", unnamed_field), "self.value"
    )
    return _UnnamedFieldRecord(
        field_type_alias_element=_py_type_from_idl(idl, unnamed_field),
        value_type_alias_element=_py_type_from_idl(
            idl, unnamed_field, use_fields_interface_for_struct=False
        ),
        json_interface_value_element=_idl_type_to_json_type(unnamed_field),
        tuple_element=_struct_field_initializer(
            idl, _IdlField(elem_name, unnamed_field), ""
        ),
        json_value_element=_field_to_json(idl, _IdlField(elem_name, unnamed_field)),
        encodable_value_item=StrDictEntry(f"_{index}", encodable),
        init_element_for_from_decoded=_field_from_decoded(
            idl, _IdlField(f'val["_{index}"]', unnamed_field), ""
        ),
        init_element_for_from_json=_field_from_json(
            _IdlField(f'value["{index}"]', unnamed_field),
        ),
    )


def gen_enum(idl: Idl, name: str, variants: list[_IdlEnumVariant]) -> str:
    imports = Suite(
        [
            Import("typing"),
            FromImport("dataclasses", ["dataclass"]),
            FromImport("construct", ["Container"]),
            FromImport("solana.publickey", ["PublicKey"]),
            FromImport("anchorpy.borsh_extension", ["EnumForCodegen"]),
            ImportAs("borsh_construct", "borsh"),
            FromImport("..", ["types"]),
        ]
    )
    invalid_enum_raise = Raise('ValueError("Invalid enum object")')
    from_decoded_dict_check = If("not isinstance(obj, dict)", invalid_enum_raise)
    variant_name_in_obj_checks: list[Generable] = []
    obj_kind_checks: list[Generable] = []
    json_interfaces: list[TypedDict] = []
    classes: list[Class] = []
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
        cstruct_fields: dict[str, str] = {}
        to_json_items_base = StrDictEntry("kind", f'"{variant.name}"')
        json_interface_kind_field = TypedParam(
            "kind", f'typing.Literal["{variant.name}"]'
        )
        cstructs: list[str] = []

        def make_variant_name_in_obj_check(then: Generable) -> Generable:
            return If(f'"{variant.name}" in obj', then)

        def make_obj_kind_check(return_val: str) -> Generable:
            return If(f'kind == "{variant.name}"', Return(return_val))

        if fields:
            val_line_for_from_decoded = Assign("val", f'obj["{variant.name}"]')
            if isinstance(fields[0], _IdlField):
                named_enum_fields = cast(_IdlEnumFieldsNamed, fields)
                field_type_alias_entries: list[TypedParam] = []
                value_type_alias_entries: list[TypedParam] = []
                json_interface_value_type_entries: list[TypedParam] = []
                init_method_body_items: list[StrDictEntry] = []
                json_value_items: list[StrDictEntry] = []
                init_entries_for_from_decoded: list[StrDictEntry] = []
                init_entries_for_from_json: list[StrDictEntry] = []
                for named_field in named_enum_fields:
                    rec = _make_named_field_record(named_field, idl)
                    field_type_alias_entries.append(rec.field_type_alias_entry)
                    value_type_alias_entries.append(rec.value_type_alias_entry)
                    json_interface_value_type_entries.append(
                        rec.json_interface_value_type_entry
                    )
                    init_method_body_items.append(rec.init_method_body_item)
                    json_value_items.append(rec.json_value_item)
                    encodable_value_items.append(rec.encodable_value_item)
                    init_entries_for_from_decoded.append(
                        rec.init_entry_for_from_decoded
                    )
                    init_entries_for_from_json.append(rec.init_entry_for_from_json)

                    cstruct_fields[named_field.name] = _layout_for_type(
                        named_field.type
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
                init_method_body = Assign(
                    "self.value",
                    StrDict(init_method_body_items),
                )
                json_value_entry = StrDict(json_value_items)
                to_json_body = Return(
                    StrDict(
                        [to_json_items_base, StrDictEntry("value", json_value_entry)]
                    )
                )
                init_arg_for_from_decoded = StrDict(init_entries_for_from_decoded)
                init_arg_for_from_json = StrDict(init_entries_for_from_json)
            else:
                tuple_enum_fields = cast(_IdlEnumFieldsTuple, fields)
                field_type_alias_elements: list[str] = []
                value_type_alias_elements: list[str] = []
                json_interface_value_elements: list[str] = []
                tuple_elements: list[str] = []
                json_value_elements: list[str] = []
                init_elements_for_from_decoded: list[str] = []
                init_elements_for_from_json: list[str] = []
                for i, unnamed_field in enumerate(tuple_enum_fields):
                    rec_unnamed = _make_unnamed_field_record(i, unnamed_field, idl)
                    field_type_alias_elements.append(
                        rec_unnamed.field_type_alias_element
                    )
                    value_type_alias_elements.append(
                        rec_unnamed.value_type_alias_element
                    )
                    json_interface_value_elements.append(
                        rec_unnamed.json_interface_value_element
                    )
                    tuple_elements.append(rec_unnamed.tuple_element)
                    json_value_elements.append(rec_unnamed.json_value_element)
                    encodable_value_items.append(rec_unnamed.encodable_value_item)
                    init_elements_for_from_decoded.append(
                        rec_unnamed.init_element_for_from_decoded
                    )
                    init_elements_for_from_json.append(
                        rec_unnamed.init_element_for_from_json
                    )
                    cstruct_fields[f"_{i}"] = _layout_for_type(unnamed_field)
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
                    Tuple(tuple_elements),
                )
                to_json_body = Return(
                    StrDict(
                        [
                            to_json_items_base,
                            StrDictEntry("value", str(List(json_value_elements))),
                        ]
                    )
                )
                init_arg_for_from_decoded = Tuple(init_elements_for_from_decoded)
                init_arg_for_from_json = Tuple(init_elements_for_from_json)
            init_method = InitMethod(
                [TypedParam("value", fields_interface_name)], init_method_body
            )
            init_method_container = [init_method]
            to_json_method = Method("to_json", [], to_json_body, json_interface_name)
            encodable_value_entry = StrDict(encodable_value_items)
            to_encodable_body = Return(
                StrDict([StrDictEntry(variant.name, encodable_value_entry)])
            )
            to_encodable_method = Method("to_encodable", [], to_encodable_body, "dict")
            json_interface_params = [
                TypedParam("value", json_interface_value_field_type.name),
                json_interface_kind_field,
            ]
            variant_name_in_obj_check = make_variant_name_in_obj_check(
                Suite(
                    [
                        val_line_for_from_decoded,
                        Return(f"{variant.name}({init_arg_for_from_decoded})"),
                    ]
                )
            )
            obj_kind_check = make_obj_kind_check(
                f"{variant.name}({init_arg_for_from_json})",
            )
        else:
            to_json_method = ClassMethod(
                "to_json",
                [],
                Return(StrDict([to_json_items_base])),
                json_interface_name,
            )
            to_encodable_method = ClassMethod(
                "to_encodable",
                [],
                Return(StrDict([StrDictEntry(variant.name, StrDict([]))])),
                "dict",
            )
            init_method_container = []
            json_interface_params = [json_interface_kind_field]
            variant_name_in_obj_check = make_variant_name_in_obj_check(
                Return(f"{variant.name}()")
            )
            obj_kind_check = make_obj_kind_check(f"{variant.name}()")
        json_interfaces.append(TypedDict(json_interface_name, json_interface_params))
        class_common_attrs = [
            Assign("discriminator", discriminator),
            Assign("kind", f'"{variant.name}"'),
        ]

        attrs = [
            *class_common_attrs,
            *init_method_container,
            to_json_method,
            to_encodable_method,
        ]
        classes.append(Class(variant.name, None, attrs))
        variant_name_in_obj_checks.append(variant_name_in_obj_check)
        obj_kind_checks.append(obj_kind_check)
        cstructs.append(f'"{variant.name}" / {_make_cstruct(cstruct_fields)}')
    from_decoded_fn = Function(
        "from_decoded",
        [TypedParam("obj", "dict")],
        Suite(
            [from_decoded_dict_check, *variant_name_in_obj_checks, invalid_enum_raise]
        ),
        f"types.{_kind_interface_name(name)}",
    )
    from_json_fn = Function(
        "from_json",
        [TypedParam("obj", f"types.{_json_interface_name(name)}")],
        Suite(
            [
                Assign("kind", 'obj["kind"]'),
                *obj_kind_checks,
                Raise("ValueError(Uncrecognized enum kind: kind)"),
            ]
        ),
        _kind_interface_name(name),
    )
    formatted_cstructs = ",".join(cstructs)
    layout_fn = Function(
        "layout", [], Return(f"EnumForCodegen({formatted_cstructs})"), "EnumForCodegen"
    )
    return str(
        Suite(
            [
                imports,
                *extra_aliases,
                *fields_type_aliases,
                *value_type_aliases,
                *json_interfaces,
                *classes,
                from_decoded_fn,
                from_json_fn,
                layout_fn,
            ]
        )
    )
