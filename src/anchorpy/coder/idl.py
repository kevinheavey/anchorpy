"""IDL coding."""
from dataclasses import make_dataclass
from types import MappingProxyType
from keyword import kwlist
from typing import List, Mapping, Optional, Union, cast, Type, Tuple
from solana.publickey import PublicKey

from construct import Construct
from borsh_construct import (
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

from anchorpy.borsh_extension import PublicKey as BorshPublicKey, DataclassStruct
from anchorpy.idl import (
    IdlEnumFieldsNamed,
    IdlField,
    IdlType,
    IdlTypeArray,
    IdlTypeDef,
    IdlTypeDefTy,
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
        "publicKey": BorshPublicKey,
    },
)


FIELD_PYTHON_TYPE_MAP: Mapping[str, Type] = MappingProxyType(
    {
        "bool": bool,
        "u8": int,
        "i8": int,
        "u16": int,
        "i16": int,
        "u32": int,
        "i32": int,
        "u64": int,
        "i64": int,
        "u128": int,
        "i128": int,
        "bytes": bytes,
        "string": str,
        "publicKey": PublicKey,
    },
)


def _handle_enum_variants(
    idl_enum: IdlTypeDefTyEnum,
    types: List[IdlTypeDef],
    name: str,
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
            named_fields = cast(IdlEnumFieldsNamed, variant_fields)
            cstruct = CStruct(*fields)
            datacls = idl_enum_fields_named_to_dataclass_type(
                named_fields,
                types,
                variant_name,
            )
            variants.append(variant_name / DataclassStruct(cstruct, datacls=datacls))  # type: ignore
    return Enum(*variants, enum_name=name)


def typedef_layout(
    typedef: IdlTypeDef,
    types: List[IdlTypeDef],
    name: str = "",
) -> Construct:
    typedef_type = typedef.type
    if isinstance(typedef_type, IdlTypeDefTyStruct):
        field_layouts = [field_layout(field, types) for field in typedef_type.fields]
        cstruct = CStruct(*field_layouts)
        datacls = idl_typedef_ty_struct_to_dataclass_type(typedef_type, types, name)
        return name / DataclassStruct(cstruct, datacls=datacls)
    elif isinstance(typedef_type, IdlTypeDefTyEnum):
        return name / _handle_enum_variants(typedef_type, types, name)
    unknown_type = typedef_type.kind
    raise ValueError(f"Unknown type {unknown_type}")


def field_layout(field: IdlField, types: List[IdlTypeDef]) -> Construct:
    """Map IDL spec to `borsh-construct` types.

    Args:
        field: field object from the IDL.
        types: IDL type definitions.

    Returns:
        `Construct` object from `borsh-construct`.
    """
    field_name = field.name if field.name else ""
    if isinstance(field.type, str):
        return field_name / FIELD_TYPE_MAP[field.type]
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


def idl_type_to_python_type(
    idl_type: IdlType,
    types: List[IdlTypeDef],
    defined_field_name: str = "",
) -> Type:
    if isinstance(idl_type, str):
        return FIELD_PYTHON_TYPE_MAP[idl_type]
    compound_idl_type = cast(
        NonLiteralIdlTypes,
        idl_type,
    )
    if isinstance(compound_idl_type, IdlTypeVec):
        return list[idl_type_to_python_type(compound_idl_type.vec, types)]
    elif isinstance(compound_idl_type, IdlTypeOption):
        return Optional[idl_type_to_python_type(compound_idl_type.option, types)]
    elif isinstance(compound_idl_type, IdlTypeArray):
        array_ty = compound_idl_type.array[0]
        array_len = compound_idl_type.array[1]
        return tuple[
            (
                idl_type_to_python_type(
                    array_ty,
                    types,
                ),
            )
            * array_len
        ]
    elif isinstance(compound_idl_type, IdlTypeDefined):
        defined = compound_idl_type.defined
        if not types:
            raise ValueError("User defined types not provided")
        filtered = [t for t in types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        return idl_typedef_type_to_python_type(
            filtered[0].type,
            types,
            defined_field_name,
        )


def idl_typedef_ty_struct_to_dataclass_type(
    typedef_type: IdlTypeDefTyStruct,
    types: List[IdlTypeDef],
    name: str,
) -> Type:
    dataclass_fields = []
    for field in typedef_type.fields:
        field_name = field.name
        field_name_to_use = f"{field_name}_" if field_name in kwlist else field_name
        dataclass_fields.append(
            (field_name_to_use, idl_type_to_python_type(field.type, types)),
        )
    return make_dataclass(name, dataclass_fields)


def idl_enum_fields_named_to_dataclass_type(
    fields: IdlEnumFieldsNamed,
    types: List[IdlTypeDef],
    name: str,
) -> Type:
    dataclass_fields = []
    for field in fields:
        field_name = field.name
        field_name_to_use = f"{field_name}_" if field_name in kwlist else field_name
        dataclass_fields.append(
            (field_name_to_use, idl_type_to_python_type(field.type, types)),
        )
    return make_dataclass(name, dataclass_fields)


def idl_typedef_type_to_python_type(
    typedef_type: IdlTypeDefTy,
    types: List[IdlTypeDef],
    name: str,
) -> Type:
    if isinstance(typedef_type, IdlTypeDefTyStruct):
        return idl_typedef_ty_struct_to_dataclass_type(typedef_type, types, name)
    elif isinstance(typedef_type, IdlTypeDefTyEnum):
        return _handle_enum_variants(typedef_type, types, name).enum
    unknown_type = typedef_type.kind
    raise ValueError(f"Unknown type {unknown_type}")
