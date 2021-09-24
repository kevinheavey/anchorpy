from typing import List, Mapping, cast, Union
from types import MappingProxyType
from dataclasses import fields

from construct import Construct
from borsh import (
    CStruct,
    Enum,
    Vec,
    Bool,
    U8,
    I8,
    U16,
    I16,
    U32,
    I32,
    U64,
    I64,
    U128,
    I128,
    Bytes,
    String,
    Option,
)
from anchorpy.borsh_extension import PublicKey
from anchorpy.idl import (
    IdlField,
    IdlTypeArray,
    IdlTypeDef,
    IdlTypeDefTyEnum,
    IdlTypeDefined,
    IdlTypeOption,
    IdlTypeVec,
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
        "u64": U64,
        "i64": I64,
        "u128": U128,
        "i128": I128,
        "bytes": Bytes,
        "string": String,
        "publicKey": PublicKey,
    },
)


def _handle_enum_variants(typedef: IdlTypeDef, types: List[IdlTypeDef]) -> Enum:
    variants = []
    idl_enum = cast(IdlTypeDefTyEnum, typedef.type)
    for variant in idl_enum.variants:
        name = variant.name
        if variant.fields is None:
            variants.append(name)
        else:
            fields_ = []
            variant_fields = variant.fields
            for fld in variant_fields:
                if not hasattr(fld, "name"):  # noqa: WPS421
                    raise NotImplementedError("Tuple enum variants not yet implemented")
                named_field = cast(IdlField, fld)
                fields_.append(field_layout(named_field, types))
            variants.append(name / CStruct(*fields))
    return name / Enum(*variants)


def typedef_layout(
    typedef: IdlTypeDef,
    types: List[IdlTypeDef],
    name: str = "",
) -> Construct:
    if typedef.type.kind == "struct":
        field_layouts = [field_layout(field, types) for field in typedef.type.fields]
        return name / CStruct(*field_layouts)
    elif typedef.type.kind == "enum":
        return _handle_enum_variants(typedef, types)
    unknown_type = typedef.type.kind
    raise ValueError(f"Unknown type {unknown_type}")


def field_layout(field: IdlField, types: List[IdlTypeDef]) -> Construct:
    field_name = field.name if field.name else ""
    if field.type in FIELD_TYPE_MAP:
        field_type_str = cast(str, field.type)
        return field_name / FIELD_TYPE_MAP[field_type_str]
    field_type = cast(
        Union[IdlTypeVec, IdlTypeOption, IdlTypeDefined, IdlTypeArray],
        field.type,
    )
    type_ = fields(field_type)[0].name
    if type_ == "vec":
        field_type_vec = cast(IdlTypeVec, field.type)
        return field_name / Vec(
            field_layout(IdlField(name="", type=field_type_vec.vec), types),
        )
    elif type_ == "option":
        field_type_option = cast(IdlTypeOption, field.type)
        return field_name / Option(
            field_layout(IdlField(name="", type=field_type_option.option), types)
        )
    elif type_ == "defined":
        field_type_defined = cast(IdlTypeDefined, field.type)
        defined = field_type_defined.defined
        if not types:
            raise ValueError("User defined types not provided")
        filtered = [t for t in types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        return typedef_layout(filtered[0], types, field_name)
    elif type_ == "array":
        field_type_array = cast(IdlTypeArray, field.type)
        array_ty = field_type_array.array[0]
        array_len = field_type_array.array[1]
        inner_layout = field_layout(IdlField(name="", type=array_ty), types)
        return field_name / inner_layout[array_len]
    raise ValueError(f"Field {field} not implemented yet")
