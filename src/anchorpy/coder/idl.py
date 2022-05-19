"""IDL coding."""
from dataclasses import make_dataclass, fields as dc_fields
from types import MappingProxyType
from keyword import kwlist
from typing import Mapping, cast, Type

from construct import Construct
from borsh_construct import (
    CStruct,
    TupleStruct,
    Vec,
    Enum,
    Bool,
    U8,
    I8,
    U16,
    I16,
    U32,
    I32,
    F32,
    U64,
    I64,
    F64,
    U128,
    I128,
    Bytes,
    String,
    Option,
)

from anchorpy.borsh_extension import BorshPubkey, _DataclassStruct, COption
from anchorpy.idl import (
    _IdlEnumFieldsNamed,
    _IdlEnumFieldsTuple,
    _IdlField,
    _IdlType,
    _IdlTypeArray,
    _IdlTypeDef,
    _IdlTypeDefTyEnum,
    _IdlTypeDefTyStruct,
    _IdlTypeDefined,
    _IdlTypeOption,
    _IdlTypeCOption,
    _IdlTypeVec,
    _NonLiteralIdlTypes,
    _AccountDefOrTypeDef,
    _AccountDefsOrTypeDefs,
)


FIELD_TYPE_MAP: Mapping[str, Construct] = MappingProxyType(
    {
        "bool": Bool,
        "u8": U8,
        "i8": I8,
        "u16": U16,
        "i16": I16,
        "u32": U32,
        "i32": I32,
        "f32": F32,
        "u64": U64,
        "i64": I64,
        "f64": F64,
        "u128": U128,
        "i128": I128,
        "bytes": Bytes,
        "string": String,
        "publicKey": BorshPubkey,
    },
)


_enums_cache: dict[tuple[str, str], Enum] = {}


def _handle_enum_variants(
    idl_enum: _IdlTypeDefTyEnum,
    types: _AccountDefsOrTypeDefs,
    name: str,
) -> Enum:
    dict_key = (name, str(idl_enum))
    try:
        return _enums_cache[dict_key]
    except KeyError:
        result = _handle_enum_variants_no_cache(idl_enum, types, name)
        _enums_cache[dict_key] = result
        return result


def _handle_enum_variants_no_cache(
    idl_enum: _IdlTypeDefTyEnum,
    types: _AccountDefsOrTypeDefs,
    name: str,
) -> Enum:
    variants = []
    dclasses = {}
    for variant in idl_enum.variants:
        variant_name = variant.name
        if variant.fields is None:
            variants.append(variant_name)
        else:
            variant_fields = variant.fields
            if isinstance(variant_fields[0], _IdlField):
                fields = []
                named_fields = cast(_IdlEnumFieldsNamed, variant_fields)
                for fld in named_fields:
                    fields.append(_field_layout(fld, types))
                cstruct = CStruct(*fields)
                datacls = _idl_enum_fields_named_to_dataclass_type(
                    named_fields,
                    variant_name,
                )
                dclasses[variant_name] = datacls
                renamed = variant_name / cstruct
            else:
                fields = []
                unnamed_fields = cast(_IdlEnumFieldsTuple, variant_fields)
                for type_ in unnamed_fields:
                    fields.append(_type_layout(type_, types))
                tuple_struct = TupleStruct(*fields)
                renamed = variant_name / tuple_struct
            variants.append(renamed)  # type: ignore
    enum_without_types = Enum(*variants, enum_name=name)
    if dclasses:
        for cname in enum_without_types.enum._sumtype_constructor_names:
            try:
                dclass = dclasses[cname]
            except KeyError:
                continue
            dclass_fields = dc_fields(dclass)
            constructr = getattr(enum_without_types.enum, cname)
            for constructor_field in constructr._sumtype_attribs:
                attrib = constructor_field[1]  # type: ignore
                fld_name = constructor_field[0]  # type: ignore
                dclass_field = [f for f in dclass_fields if f.name == fld_name][0]
                attrib.type = dclass_field.type  # type: ignore
    return enum_without_types


def _typedef_layout_without_field_name(
    typedef: _AccountDefOrTypeDef,
    types: _AccountDefsOrTypeDefs,
) -> Construct:
    typedef_type = typedef.type
    name = typedef.name
    if isinstance(typedef_type, _IdlTypeDefTyStruct):
        field_layouts = [_field_layout(field, types) for field in typedef_type.fields]
        cstruct = CStruct(*field_layouts)
        datacls = _idl_typedef_ty_struct_to_dataclass_type(typedef_type, name)
        return _DataclassStruct(cstruct, datacls=datacls)
    elif isinstance(typedef_type, _IdlTypeDefTyEnum):
        return _handle_enum_variants(typedef_type, types, name)
    unknown_type = typedef_type.kind
    raise ValueError(f"Unknown type {unknown_type}")


def _typedef_layout(
    typedef: _AccountDefOrTypeDef,
    types: list[_IdlTypeDef],
    field_name: str,
) -> Construct:
    """Map an IDL typedef to a `Construct` object.

    Args:
        typedef: The IDL typedef object.
        types: IDL type definitions.
        field_name: The name of the field.

    Raises:
        ValueError: If an unknown type is passed.

    Returns:
        `Construct` object from `borsh-construct`.
    """  # noqa: DAR402
    return field_name / _typedef_layout_without_field_name(typedef, types)


def _type_layout(type_: _IdlType, types: _AccountDefsOrTypeDefs) -> Construct:
    if isinstance(type_, str):
        return FIELD_TYPE_MAP[type_]
    field_type = cast(
        _NonLiteralIdlTypes,
        type_,
    )
    if isinstance(field_type, _IdlTypeVec):
        return Vec(_type_layout(field_type.vec, types))
    elif isinstance(field_type, _IdlTypeOption):
        return Option(_type_layout(field_type.option, types))
    elif isinstance(field_type, _IdlTypeCOption):
        return COption(_type_layout(field_type.coption, types))
    elif isinstance(field_type, _IdlTypeDefined):
        defined = field_type.defined
        if not types:
            raise ValueError("User defined types not provided")
        filtered = [t for t in types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        return _typedef_layout_without_field_name(filtered[0], types)
    elif isinstance(field_type, _IdlTypeArray):
        array_ty = field_type.array[0]
        array_len = field_type.array[1]
        inner_layout = _type_layout(array_ty, types)
        return inner_layout[array_len]
    raise ValueError(f"Type {field_type} not implemented yet")


def _field_layout(field: _IdlField, types: _AccountDefsOrTypeDefs) -> Construct:
    """Map IDL spec to `borsh-construct` types.

    Args:
        field: field object from the IDL.
        types: IDL type definitions.

    Raises:
        ValueError: If the user-defined types are not provided.
        ValueError: If the type is not found.
        ValueError: If the type is not implemented yet.

    Returns:
        `Construct` object from `borsh-construct`.
    """  # noqa: DAR402
    field_name = field.name if field.name else ""
    return field_name / _type_layout(field.type, types)


def _make_datacls(name: str, fields: list[str]) -> type:
    return make_dataclass(name, fields)


_idl_typedef_ty_struct_to_dataclass_type_cache: dict[tuple[str, str], Type] = {}


def _idl_typedef_ty_struct_to_dataclass_type(
    typedef_type: _IdlTypeDefTyStruct,
    name: str,
) -> Type:
    dict_key = (name, str(typedef_type))
    try:
        return _idl_typedef_ty_struct_to_dataclass_type_cache[dict_key]
    except KeyError:
        result = _idl_typedef_ty_struct_to_dataclass_type_no_cache(typedef_type, name)
        _idl_typedef_ty_struct_to_dataclass_type_cache[dict_key] = result
        return result


def _idl_typedef_ty_struct_to_dataclass_type_no_cache(
    typedef_type: _IdlTypeDefTyStruct,
    name: str,
) -> Type:
    """Generate a dataclass definition from an IDL struct.

    Args:
        typedef_type: The IDL type.
        name: The name of the dataclass.

    Returns:
        Dataclass definition.
    """
    dataclass_fields = []
    for field in typedef_type.fields:
        field_name = field.name
        field_name_to_use = f"{field_name}_" if field_name in kwlist else field_name
        dataclass_fields.append(
            field_name_to_use,
        )
    return _make_datacls(name, dataclass_fields)


_idl_enum_fields_named_to_dataclass_type_cache: dict[tuple[str, str], Type] = {}


def _idl_enum_fields_named_to_dataclass_type(
    fields: _IdlEnumFieldsNamed,
    name: str,
) -> Type:
    dict_key = (name, str(fields))
    try:
        return _idl_enum_fields_named_to_dataclass_type_cache[dict_key]
    except KeyError:
        result = _idl_enum_fields_named_to_dataclass_type_no_cache(fields, name)
        _idl_enum_fields_named_to_dataclass_type_cache[dict_key] = result
        return result


def _idl_enum_fields_named_to_dataclass_type_no_cache(
    fields: _IdlEnumFieldsNamed,
    name: str,
) -> Type:
    """Generate a dataclass definition from IDL named enum fields.

    Args:
        fields: The IDL enum fields.
        name: The name of the dataclass.

    Returns:
        Dataclass type definition.
    """
    dataclass_fields = []
    for field in fields:
        field_name = field.name
        field_name_to_use = f"{field_name}_" if field_name in kwlist else field_name
        dataclass_fields.append(
            field_name_to_use,
        )
    return _make_datacls(name, dataclass_fields)


def _idl_typedef_to_python_type(
    typedef: _AccountDefOrTypeDef,
    types: _AccountDefsOrTypeDefs,
) -> Type:
    """Generate Python type from IDL user-defined type.

    Args:
        typedef: The user-defined type.
        types: IDL type definitions.

    Raises:
        ValueError: If an unknown type is passed.

    Returns:
        The Python type.
    """
    typedef_type = typedef.type
    if isinstance(typedef_type, _IdlTypeDefTyStruct):
        return _idl_typedef_ty_struct_to_dataclass_type(
            typedef_type,
            typedef.name,
        )
    elif isinstance(typedef_type, _IdlTypeDefTyEnum):
        return _handle_enum_variants(typedef_type, types, typedef.name).enum
    unknown_type = typedef_type.kind
    raise ValueError(f"Unknown type {unknown_type}")
