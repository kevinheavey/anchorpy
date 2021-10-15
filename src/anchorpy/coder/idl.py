"""IDL coding."""
from types import MappingProxyType
from typing import List, Mapping, cast

from construct import Construct
from borsh_construct_tmp import (
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
    IdlTypeDefTyStruct,
    IdlTypeDefined,
    IdlTypeOption,
    IdlTypeVec,
    NonLiteralIdlTypes,
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


def _handle_enum_variants(
    idl_enum: IdlTypeDefTyEnum, types: List[IdlTypeDef], name: str
) -> Enum:
    variants = []
    for variant in idl_enum.variants:
        variant_name = variant.name
        if variant.fields is None:
            variants.append(variant_name)
        else:
            fields = []
            variant_fields = variant.fields
            for fld in variant_fields:
                if not isinstance(fld, IdlField):  # noqa: WPS421
                    raise NotImplementedError("Tuple enum variants not yet implemented")
                fields.append(field_layout(fld, types))
            variants.append(variant_name / CStruct(*fields))  # type: ignore
    return Enum(*variants, enum_name=name)


def typedef_layout(
    typedef: IdlTypeDef,
    types: List[IdlTypeDef],
    name: str = "",
) -> Construct:
    typedef_type = typedef.type
    if isinstance(typedef_type, IdlTypeDefTyStruct):
        field_layouts = [field_layout(field, types) for field in typedef_type.fields]
        return name / CStruct(*field_layouts)
    elif isinstance(typedef_type, IdlTypeDefTyEnum):
        return name / _handle_enum_variants(typedef_type, types, name)
    unknown_type = typedef_type.kind
    raise ValueError(f"Unknown type {unknown_type}")


def field_layout(field: IdlField, types: List[IdlTypeDef]) -> Construct:
    field_name = field.name if field.name else ""
    if field.type in FIELD_TYPE_MAP:
        field_type_str = cast(str, field.type)
        return field_name / FIELD_TYPE_MAP[field_type_str]
    field_type = cast(
        NonLiteralIdlTypes,
        field.type,
    )
    if isinstance(field_type, IdlTypeVec):
        return field_name / Vec(
            field_layout(IdlField(name="", type=field_type.vec), types),
        )
    elif isinstance(field_type, IdlTypeOption):
        return field_name / Option(
            field_layout(IdlField(name="", type=field_type.option), types)
        )
    elif isinstance(field_type, IdlTypeDefined):
        defined = field_type.defined
        if not types:
            raise ValueError("User defined types not provided")
        filtered = [t for t in types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        return typedef_layout(filtered[0], types, field_name)
    elif isinstance(field_type, IdlTypeArray):
        array_ty = field_type.array[0]
        array_len = field_type.array[1]
        inner_layout = field_layout(IdlField(name="", type=array_ty), types)
        return field_name / inner_layout[array_len]
    raise ValueError(f"Field {field} not implemented yet")
