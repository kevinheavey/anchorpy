from typing import Dict, Union, cast
import hashlib

from anchorpy.idl import (
    Idl,
    IdlType,
    IdlTypeDef,
    IdlTypeOption,
    IdlTypeArray,
    IdlTypeDefined,
    IdlTypeVec,
    LiteralStrings,
)


def sighash(namespace: str, ix_name: str) -> bytes:
    """
    // Not technically sighash, since we don't include the arguments, as Rust
    // doesn't allow function overloading.
    export function sighash(nameSpace: string, ixName: string): Buffer {
      let name = snakeCase(ixName);
      let preimage = `${nameSpace}:${name}`;
      return Buffer.from(sha256.digest(preimage)).slice(0, 8);
    }
    """
    formatted_str = f"{namespace}:{ix_name}"
    digest = bytes(hashlib.sha256(formatted_str.encode("utf-8")).digest())
    return digest[:8]


def type_size(idl: Idl, ty: IdlType) -> int:
    """Return the size of the type in bytes.

    For variable length types, just return 1. Users should override this value in such cases.
    """
    sizes: Dict[Union[LiteralStrings, IdlTypeVec], int] = {
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
        if ty is IdlTypeOption:
            option_ty = cast(IdlTypeOption, ty)
            return 1 + type_size(idl, option_ty.option)
        if ty is IdlTypeDefined:
            field_type_defined = cast(IdlTypeDefined, ty)
            defined = field_type_defined.defined
            filtered = [t for t in idl.types if t.name == defined]
            if len(filtered) != 1:
                raise ValueError(f"Type not found {field_type_defined}")
            type_def = filtered[0]
            return account_size(idl, type_def)
        if ty is IdlTypeArray:
            array_ty = cast(IdlTypeArray, ty)
            element_type = array_ty.array[0]
            array_size = array_ty.array[1]
            return type_size(idl, element_type) * array_size
        raise ValueError(f"type_size not implemented for {ty}")


def account_size(idl: Idl, idl_account: IdlTypeDef) -> int:
    if idl_account.type.kind == "enum":
        raise Exception("account_size not implemented for enum")
    if not idl_account.type.fields:
        return 0
    return sum([type_size(idl, f.type) for f in idl_account.type.fields])
