"""Common utilities for encoding and decoding."""
from hashlib import sha256
from typing import Dict, Union

from anchorpy_core.idl import (
    Idl,
    IdlEnumVariant,
    IdlField,
    IdlType,
    IdlTypeArray,
    IdlTypeCompound,
    IdlTypeDefined,
    IdlTypeDefinition,
    IdlTypeDefinitionTyEnum,
    IdlTypeOption,
    IdlTypeSimple,
    IdlTypeVec,
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


def _type_size_compound_type(idl: Idl, ty: IdlTypeCompound) -> int:
    if isinstance(ty, IdlTypeVec):
        return 1
    if isinstance(ty, IdlTypeOption):
        return 1 + _type_size(idl, ty.option)
    if isinstance(ty, IdlTypeDefined):
        defined = ty.defined
        filtered = [t for t in idl.types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {ty}")
        type_def = filtered[0]
        return _account_size(idl, type_def)
    if isinstance(ty, IdlTypeArray):
        element_type = ty.array[0]
        array_size = ty.array[1]
        return _type_size(idl, element_type) * array_size
    raise ValueError(f"type_size not implemented for {ty}")


def _type_size(idl: Idl, ty: IdlType) -> int:
    """Return the size of the type in bytes.

    For variable length types, just return 1.
    Users should override this value in such cases.

    Args:
        idl: The parsed `Idl` object.
        ty: The type object from the IDL.

    Returns:
        The size of the object in bytes.
    """
    sizes: Dict[IdlTypeSimple, int] = {
        IdlTypeSimple.Bool: 1,
        IdlTypeSimple.U8: 1,
        IdlTypeSimple.I8: 1,
        IdlTypeSimple.Bytes: 1,
        IdlTypeSimple.String: 1,
        IdlTypeSimple.I16: 2,
        IdlTypeSimple.U16: 2,
        IdlTypeSimple.U32: 4,
        IdlTypeSimple.I32: 4,
        IdlTypeSimple.F32: 4,
        IdlTypeSimple.U64: 8,
        IdlTypeSimple.I64: 8,
        IdlTypeSimple.F64: 8,
        IdlTypeSimple.U128: 16,
        IdlTypeSimple.I128: 16,
        IdlTypeSimple.PublicKey: 32,
    }
    if isinstance(ty, IdlTypeSimple):
        return sizes[ty]
    return _type_size_compound_type(idl, ty)


def _variant_field_size(idl: Idl, field: Union[IdlField, IdlType]) -> int:
    if isinstance(field, IdlField):
        return _type_size(idl, field.ty)
    return _type_size(idl, field)


def _variant_size(idl: Idl, variant: IdlEnumVariant) -> int:
    if variant.fields is None:
        return 0
    field_sizes = []
    field: Union[IdlField, IdlType]
    for field in variant.fields.fields:
        field_sizes.append(_variant_field_size(idl, field))
    return sum(field_sizes)


def _account_size(idl: Idl, idl_account: IdlTypeDefinition) -> int:
    """Calculate account size in bytes.

    Args:
        idl: The parsed `Idl` instance.
        idl_account: An item from `idl.accounts`.

    Returns:
        Account size.
    """
    idl_account_type = idl_account.ty
    if isinstance(idl_account_type, IdlTypeDefinitionTyEnum):
        variant_sizes = (
            _variant_size(idl, variant) for variant in idl_account_type.variants
        )
        return max(variant_sizes) + 1
    if idl_account_type.fields is None:
        return 0
    return sum(_type_size(idl, f.ty) for f in idl_account_type.fields)
