"""IDL coding."""
from dataclasses import fields as dc_fields
from dataclasses import make_dataclass
from keyword import kwlist
from types import MappingProxyType
from typing import Mapping, Type, cast

from anchorpy_core.idl import (
    IdlField,
    IdlType,
    IdlTypeArray,
    IdlTypeDefined,
    IdlTypeDefinition,
    IdlTypeDefinitionTyAlias,
    IdlTypeDefinitionTyEnum,
    IdlTypeDefinitionTyStruct,
    IdlTypeOption,
    IdlTypeSimple,
    IdlTypeVec,
)
from borsh_construct import (
    F32,
    F64,
    I8,
    I16,
    I32,
    I64,
    I128,
    U8,
    U16,
    U32,
    U64,
    U128,
    Bool,
    Bytes,
    CStruct,
    Enum,
    Option,
    String,
    TupleStruct,
    Vec,
)
from construct import Construct
from pyheck import snake

from anchorpy.borsh_extension import BorshPubkey, _DataclassStruct
from anchorpy.idl import TypeDefs

FIELD_TYPE_MAP: Mapping[IdlTypeSimple, Construct] = MappingProxyType(
    {
        IdlTypeSimple.Bool: Bool,
        IdlTypeSimple.U8: U8,
        IdlTypeSimple.I8: I8,
        IdlTypeSimple.U16: U16,
        IdlTypeSimple.I16: I16,
        IdlTypeSimple.U32: U32,
        IdlTypeSimple.I32: I32,
        IdlTypeSimple.F32: F32,
        IdlTypeSimple.U64: U64,
        IdlTypeSimple.I64: I64,
        IdlTypeSimple.F64: F64,
        IdlTypeSimple.U128: U128,
        IdlTypeSimple.I128: I128,
        IdlTypeSimple.Bytes: Bytes,
        IdlTypeSimple.String: String,
        IdlTypeSimple.PublicKey: BorshPubkey,
    },
)


_enums_cache: dict[tuple[str, str], Enum] = {}


def _handle_enum_variants(
    idl_enum: IdlTypeDefinitionTyEnum,
    types: TypeDefs,
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
    idl_enum: IdlTypeDefinitionTyEnum,
    types: TypeDefs,
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
            flds = variant_fields.fields
            if isinstance(flds[0], IdlField):
                fields = []
                named_fields = cast(list[IdlField], flds)
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
                unnamed_fields = cast(list[IdlType], flds)
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
    typedef: IdlTypeDefinition,
    types: TypeDefs,
) -> Construct:
    typedef_type = typedef.ty
    name = typedef.name
    if isinstance(typedef_type, IdlTypeDefinitionTyStruct):
        field_layouts = [_field_layout(field, types) for field in typedef_type.fields]
        cstruct = CStruct(*field_layouts)
        datacls = _idl_typedef_ty_struct_to_dataclass_type(typedef_type, name)
        return _DataclassStruct(cstruct, datacls=datacls)
    elif isinstance(typedef_type, IdlTypeDefinitionTyEnum):
        return _handle_enum_variants(typedef_type, types, name)
    elif isinstance(typedef_type, IdlTypeDefinitionTyAlias):
        return _type_layout(typedef_type.value, types)
    unknown_type = typedef_type.kind
    raise ValueError(f"Unknown type {unknown_type}")


def _typedef_layout(
    typedef: IdlTypeDefinition,
    types: list[IdlTypeDefinition],
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
    """
    return field_name / _typedef_layout_without_field_name(typedef, types)


def _type_layout(type_: IdlType, types: TypeDefs) -> Construct:
    if isinstance(type_, IdlTypeSimple):
        return FIELD_TYPE_MAP[type_]
    if isinstance(type_, IdlTypeVec):
        return Vec(_type_layout(type_.vec, types))
    elif isinstance(type_, IdlTypeOption):
        return Option(_type_layout(type_.option, types))
    elif isinstance(type_, IdlTypeDefined):
        defined = type_.defined
        if not types:
            raise ValueError("User defined types not provided")
        filtered = [t for t in types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        return _typedef_layout_without_field_name(filtered[0], types)
    elif isinstance(type_, IdlTypeArray):
        array_ty = type_.array[0]
        array_len = type_.array[1]
        inner_layout = _type_layout(array_ty, types)
        return inner_layout[array_len]
    raise ValueError(f"Type {type_} not implemented yet")


def _field_layout(field: IdlField, types: TypeDefs) -> Construct:
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
    """
    field_name = snake(field.name) if field.name else ""
    return field_name / _type_layout(field.ty, types)


def _make_datacls(name: str, fields: list[str]) -> type:
    return make_dataclass(name, fields)


_idl_typedef_ty_struct_to_dataclass_type_cache: dict[tuple[str, str], Type] = {}


def _idl_typedef_ty_struct_to_dataclass_type(
    typedef_type: IdlTypeDefinitionTyStruct,
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
    typedef_type: IdlTypeDefinitionTyStruct,
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
        field_name = snake(field.name)
        field_name_to_use = f"{field_name}_" if field_name in kwlist else field_name
        dataclass_fields.append(
            field_name_to_use,
        )
    return _make_datacls(name, dataclass_fields)


_idl_enum_fields_named_to_dataclass_type_cache: dict[tuple[str, str], Type] = {}


def _idl_enum_fields_named_to_dataclass_type(
    fields: list[IdlField],
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
    fields: list[IdlField],
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
        field_name = snake(field.name)
        field_name_to_use = f"{field_name}_" if field_name in kwlist else field_name
        dataclass_fields.append(
            field_name_to_use,
        )
    return _make_datacls(name, dataclass_fields)


def _idl_typedef_to_python_type(
    typedef: IdlTypeDefinition,
    types: TypeDefs,
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
    typedef_type = typedef.ty
    if isinstance(typedef_type, IdlTypeDefinitionTyStruct):
        return _idl_typedef_ty_struct_to_dataclass_type(
            typedef_type,
            typedef.name,
        )
    elif isinstance(typedef_type, IdlTypeDefinitionTyEnum):
        return _handle_enum_variants(typedef_type, types, typedef.name).enum
    elif isinstance(typedef_type, IdlTypeDefinitionTyAlias):
        raise ValueError(f"Alias not handled here: {typedef_type}")
    unknown_type = typedef_type.kind
    raise ValueError(f"Unknown type {unknown_type}")
