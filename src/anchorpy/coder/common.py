"""Common utilities for encoding and decoding."""
from typing import Dict, Union
from hashlib import sha256

from anchorpy.idl import (
    Idl,
    _IdlEnumVariant,
    _IdlField,
    _IdlType,
    _IdlTypeDefTyEnum,
    _IdlTypeOption,
    _IdlTypeCOption,
    _IdlTypeArray,
    _IdlTypeDefined,
    _IdlTypeVec,
    _LiteralStrings,
    _NonLiteralIdlTypes,
    _AccountDefOrTypeDef,
)


def _sighash(ix_name: str) -> bytes:
    """Not technically sighash, since we don't include the arguments.

    (Because Rust doesn't allow function overloading.)

    Args:
        ix_name: The instruction name.

    Returns:
        The sighash bytes.
    """
    formatted_str = f"global:{ix_name}"
    return sha256(formatted_str.encode()).digest()[:8]


def _type_size_compound_type(idl: Idl, ty: _NonLiteralIdlTypes) -> int:
    if isinstance(ty, _IdlTypeVec):
        return 1
    if isinstance(ty, _IdlTypeOption):
        return 1 + _type_size(idl, ty.option)
    if isinstance(ty, _IdlTypeCOption):
        return 4 + _type_size(idl, ty.coption)
    if isinstance(ty, _IdlTypeDefined):
        defined = ty.defined
        filtered = [t for t in idl.types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {ty}")
        type_def = filtered[0]
        return _account_size(idl, type_def)
    if isinstance(ty, _IdlTypeArray):
        element_type = ty.array[0]
        array_size = ty.array[1]
        return _type_size(idl, element_type) * array_size
    raise ValueError(f"type_size not implemented for {ty}")


def _type_size(idl: Idl, ty: _IdlType) -> int:
    """Return the size of the type in bytes.

    For variable length types, just return 1.
    Users should override this value in such cases.

    Args:
        idl: The parsed `Idl` object.
        ty: The type object from the IDL.

    Returns:
        The size of the object in bytes.
    """
    sizes: Dict[_LiteralStrings, int] = {
        "bool": 1,
        "u8": 1,
        "i8": 1,
        "bytes": 1,
        "string": 1,
        "i16": 2,
        "u16": 2,
        "u32": 4,
        "i32": 4,
        "f32": 4,
        "u64": 8,
        "i64": 8,
        "f64": 8,
        "u128": 16,
        "i128": 16,
        "publicKey": 32,
    }
    if isinstance(ty, str):
        return sizes[ty]
    return _type_size_compound_type(idl, ty)


def _variant_field_size(idl: Idl, field: Union[_IdlField, _IdlType]) -> int:
    if isinstance(field, _IdlField):
        return _type_size(idl, field.type)
    return _type_size(idl, field)


def _variant_size(idl: Idl, variant: _IdlEnumVariant) -> int:
    if variant.fields is None:
        return 0
    field_sizes = []
    field: Union[_IdlField, _IdlType]
    for field in variant.fields:
        field_sizes.append(_variant_field_size(idl, field))
    return sum(field_sizes)


def _account_size(idl: Idl, idl_account: _AccountDefOrTypeDef) -> int:
    """Calculate account size in bytes.

    Args:
        idl: The parsed `Idl` instance.
        idl_account: An item from `idl.accounts`.

    Returns:
        Account size.
    """
    idl_account_type = idl_account.type
    if isinstance(idl_account_type, _IdlTypeDefTyEnum):
        variant_sizes = (
            _variant_size(idl, variant) for variant in idl_account_type.variants
        )
        return max(variant_sizes) + 1
    if idl_account_type.fields is None:
        return 0
    return sum(_type_size(idl, f.type) for f in idl_account_type.fields)
