import hashlib

from anchorpy.idl import Idl, IdlType, IdlTypeDef


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


# Returns the size of the type in bytes. For variable length types, just return 1.
# Users should override this value in such cases.
def type_size(idl: Idl, ty: IdlType) -> int:
    if isinstance(ty, dict):
        if "vec" in ty:
            return 1
        if "option" in ty:
            raise Exception("Option not implemented")
        if "defined" in ty:
            raise Exception("Defined not implemented")
        if "array" in ty:
            raise Exception("Array  not implemented")
    elif ty in {"bool", "u8", "i8", "bytes", "string"}:
        return 1
    elif ty in {"i16", "u16"}:
        return 2
    elif ty in {"u32", "i32"}:
        return 4
    elif ty in {"u64", "i64"}:
        return 8
    elif ty in {"u128", "i128"}:
        return 16
    elif ty == "publicKey":
        return 32
    else:
        raise Exception(f"type_size not implemented for {ty}")


def account_size(idl: Idl, idl_account: IdlTypeDef) -> int:
    if idl_account.type.kind == "enum":
        raise Exception("account_size not implemented for enum")
    if not idl_account.type.fields:
        return 0
    return sum([type_size(idl, f.type) for f in idl_account.type.fields])
