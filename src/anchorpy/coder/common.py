from typing import Dict, Union
from hashlib import sha256
from inflection import underscore

from anchorpy.idl import (
    Idl,
    IdlEnumVariant,
    IdlField,
    IdlType,
    IdlTypeDef,
    IdlTypeDefTyEnum,
    IdlTypeOption,
    IdlTypeArray,
    IdlTypeDefined,
    IdlTypeVec,
    LiteralStrings,
    NonLiteralIdlTypes,
)


def sighash(namespace: str, ix_name: str) -> bytes:
    """Not technically sighash, since we don't include the arguments.

    (Because Rust doesn't allow function overloading.)"""
    formatted_str = f"{namespace}:{underscore(ix_name)}"
    return sha256(formatted_str.encode()).digest()[:8]


def _type_size_compound_type(idl: Idl, ty: NonLiteralIdlTypes) -> int:
    if isinstance(ty, IdlTypeVec):
        return 1
    if isinstance(ty, IdlTypeOption):
        return 1 + type_size(idl, ty.option)
    if isinstance(ty, IdlTypeDefined):
        defined = ty.defined
        filtered = [t for t in idl.types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {ty}")
        type_def = filtered[0]
        return account_size(idl, type_def)
    if isinstance(ty, IdlTypeArray):
        element_type = ty.array[0]
        array_size = ty.array[1]
        return type_size(idl, element_type) * array_size
    raise ValueError(f"type_size not implemented for {ty}")


def type_size(idl: Idl, ty: IdlType) -> int:
    """Return the size of the type in bytes.

    For variable length types, just return 1.
    Users should override this value in such cases.
    """
    sizes: Dict[LiteralStrings, int] = {
        "bool": 1,
        "u8": 1,
        "i8": 1,
        "bytes": 1,
        "string": 1,
        "i16": 2,
        "u16": 2,
        "u32": 4,
        "i32": 4,
        "u64": 8,
        "i64": 8,
        "u128": 16,
        "i128": 16,
        "publicKey": 32,
    }
    try:
        return sizes[ty]  # type: ignore
    except KeyError:
        return _type_size_compound_type(idl, ty)  # type: ignore


def _variant_field_size(idl: Idl, field: Union[IdlField, IdlType]) -> int:
    if isinstance(field, IdlField):
        return type_size(idl, field.type)
    return type_size(idl, field)


def _variant_size(idl: Idl, variant: IdlEnumVariant) -> int:
    if variant.fields is None:
        return 0
    field_sizes = []
    field: Union[IdlField, IdlType]
    for field in variant.fields:
        field_sizes.append(_variant_field_size(idl, field))
    return sum(field_sizes)


def account_size(idl: Idl, idl_account: IdlTypeDef) -> int:
    idl_account_type = idl_account.type
    if isinstance(idl_account_type, IdlTypeDefTyEnum):
        variant_sizes = (
            _variant_size(idl, variant) for variant in idl_account_type.variants
        )
        return max(variant_sizes) + 1
    if idl_account_type.fields is None:
        return 0
    return sum(type_size(idl, f.type) for f in idl_account_type.fields)
