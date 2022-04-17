from typing import Optional
from anchorpy.idl import (
    Idl,
    _IdlType,
    _IdlTypeVec,
    _IdlTypeOption,
    _IdlTypeCOption,
    _IdlTypeDefined,
    _IdlTypeDefTyStruct,
    _IdlTypeArray,
    _IdlField,
)


def fields_interface_name(type_name: str) -> str:
    return f"{type_name}Fields"


def value_interface_name(type_name: str) -> str:
    return f"{type_name}Value"


def kind_interface_name(type_name: str) -> str:
    return f"{type_name}Kind"


def json_interface_name(type_name: str) -> str:
    return f"{type_name}JSON"


def py_type_from_idl(
    idl: Idl,
    ty: _IdlType,
    defined_types_prefix: str = "types.",
    use_fields_interface_for_struct: bool = True,
) -> str:
    if ty == "bool":
        return "bool"
    elif ty in {"u8", "i8", "u16", "u16" "u32", "i32", "u64", "i64", "u128", "i128"}:
        return "int"
    elif ty in {"f32", "f64"}:
        return "float"
    elif ty == "bytes":
        return "bytes"
    elif ty == "string":
        return "str"
    elif ty == "publicKey":
        return "PublicKey"
    elif isinstance(ty, _IdlTypeVec):
        inner_type = py_type_from_idl(
            idl, ty.vec, defined_types_prefix, use_fields_interface_for_struct
        )
        return f"list[{inner_type}]"
    elif isinstance(ty, _IdlTypeOption):
        inner_type = py_type_from_idl(
            idl, ty.option, defined_types_prefix, use_fields_interface_for_struct
        )
        return f"Optional[{inner_type}]"
    elif isinstance(ty, _IdlTypeCOption):
        inner_type = py_type_from_idl(
            idl, ty.coption, defined_types_prefix, use_fields_interface_for_struct
        )
        return f"Optional[{inner_type}]"
    elif isinstance(ty, _IdlTypeDefined):
        defined = ty.defined
        filtered = [t for t in idl.types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        type_kind = filtered[0].type.kind
        if isinstance(type_kind, _IdlTypeDefTyStruct):
            name = (
                fields_interface_name(ty.defined)
                if use_fields_interface_for_struct
                else ty.defined
            )
            return f"{defined_types_prefix}{name}"
        name = kind_interface_name(ty.defined)
        return f"{defined_types_prefix}{name}"
    elif isinstance(ty, _IdlTypeArray):
        inner_type = py_type_from_idl(
            idl, ty.array[0], defined_types_prefix, use_fields_interface_for_struct
        )
        return f"list[{inner_type}]"
    raise ValueError(f"Unrecognized type: {ty}")


def layout_for_type(
    ty: _IdlType,
    name: Optional[str] = None,
    defined_types_prefix: str = "types.",
) -> str:
    if ty == "bool":
        inner = "borsh.Bool"
    elif ty == "u8":
        inner = "borsh.U8"
    elif ty == "i8":
        inner = "borsh.I8"
    elif ty == "u16":
        inner = "borsh.U16"
    elif ty == "i16":
        inner = "borsh.I16"
    elif ty == "u32":
        inner = "borsh.U32"
    elif ty == "f32":
        inner = "borsh.F32"
    elif ty == "i32":
        inner = "borsh.I32"
    elif ty == "u64":
        inner = "borsh.U64"
    elif ty == "i64":
        inner = "borsh.I64"
    elif ty == "f64":
        inner = "borsh.F64"
    elif ty == "u128":
        inner = "borsh.U128"
    elif ty == "i128":
        inner = "borsh.I128"
    elif ty == "bytes":
        inner = "borsh.Bytes"
    elif ty == "string":
        inner = "borsh.String"
    elif ty == "publicKey":
        inner = "_BorshPubkey"
    elif isinstance(ty, _IdlTypeVec):
        inner = f"borsh.Vec({layout_for_type(ty.vec)})"
    elif isinstance(ty, _IdlTypeOption):
        inner = f"borsh.Option({layout_for_type(ty.option)})"
    elif isinstance(ty, _IdlTypeCOption):
        inner = f"COption({layout_for_type(ty.option)})"
    elif isinstance(ty, _IdlTypeDefined):
        inner = f"{defined_types_prefix}{ty.defined}.layout()"
    elif isinstance(ty, _IdlTypeArray):
        inner = f"{layout_for_type(ty.array[0])}[{ty.array[1]}]"
    else:
        raise ValueError(f"Unrecognized type: {ty}")

    if name is None:
        return inner
    return f'"{name}" / {inner}'


def field_to_encodable(
    idl: Idl, ty: _IdlField, val_prefix: str = "", defined_types_prefix: str = "types."
) -> str:
    ty_type = ty.type
    if ty_type in {
        "bool",
        "u8",
        "i8",
        "u16",
        "i16",
        "u32",
        "i32",
        "f32",
        "u64",
        "i64",
        "f64",
        "u128",
        "i128",
        "string",
        "publicKey",
        "bytes",
    }:
        return f"{val_prefix}{ty.name}"
    if isinstance(ty_type, _IdlTypeVec):
        map_body = field_to_encodable(
            idl, _IdlField("item", ty_type.vec), "", defined_types_prefix
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty.name}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty.name}))"
    if isinstance(ty_type, _IdlTypeOption):
        encodable = field_to_encodable(
            idl, _IdlField(ty.name, ty_type.option), val_prefix, defined_types_prefix
        )
        if encodable == f"{val_prefix}{ty.name}":
            return encodable
        return f"({val_prefix}{ty.name} and {encodable}) or None"
    if isinstance(ty_type, _IdlTypeCOption):
        raise NotImplementedError("COption not implemented.")
    if isinstance(ty_type, _IdlTypeDefined):
        defined = ty_type.defined
        filtered = [t for t in idl.types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        type_kind = filtered[0].type.kind
        if isinstance(type_kind, _IdlTypeDefTyStruct):
            return (
                f"{defined_types_prefix}{defined}.to_encodable({val_prefix}{ty.name})"
            )
        return f"{val_prefix}{ty.name}.to_encodable()"
    if isinstance(ty_type, _IdlTypeArray):
        map_body = field_to_encodable(
            idl, _IdlField("item", ty_type.array[0]), "", defined_types_prefix
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty.name}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty.name}))"
    raise ValueError(f"Unrecognized type: {ty_type}")


def field_from_decoded(
    idl: Idl, ty: _IdlField, val_prefix: str = "", defined_types_prefix: str = "types."
) -> str:
    ty_type = ty.type
    if ty_type in {
        "bool",
        "u8",
        "i8",
        "u16",
        "i16",
        "u32",
        "i32",
        "f32",
        "u64",
        "i64",
        "f64",
        "u128",
        "i128",
        "string",
        "publicKey",
        "bytes",
    }:
        return f"{val_prefix}{ty.name}"
    if isinstance(ty_type, _IdlTypeVec):
        map_body = field_from_decoded(
            idl, _IdlField("item", ty_type.vec), "", defined_types_prefix
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty.name}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty.name}))"
    if isinstance(ty_type, _IdlTypeOption):
        decoded = field_from_decoded(
            idl, _IdlField(ty.name, ty_type.option), val_prefix
        )
        # skip coercion when not needed
        if decoded == f"{val_prefix}{ty.name}":
            return decoded
        return f"({val_prefix}{ty.name} and {decoded}) or None"
    if isinstance(ty_type, _IdlTypeCOption):
        raise NotImplementedError("COption not implemented.")
    if isinstance(ty_type, _IdlTypeDefined):
        defined = ty_type.defined
        filtered = [t for t in idl.types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        return f"{defined_types_prefix}${defined}.from_decoded(${val_prefix}${ty.name})"
    if isinstance(ty_type, _IdlTypeArray):
        map_body = field_from_decoded(
            idl, _IdlField("item", ty_type.array[0]), "", defined_types_prefix
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty.name}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty.name}))"
    raise ValueError(f"Unrecognized type: {ty_type}")


def struct_field_initializer(
    idl: Idl, field: _IdlField, prefix: str = "fields."
) -> str:
    field_type = field.type
    if field_type in {
        "bool",
        "u8",
        "i8",
        "u16",
        "i16",
        "u32",
        "i32",
        "f32",
        "u64",
        "i64",
        "f64",
        "u128",
        "i128",
        "string",
        "publicKey",
        "bytes",
    }:
        return f"{prefix}{field.name}"
    if isinstance(field_type, _IdlTypeDefined):
        defined = field_type.defined
        filtered = [t for t in idl.types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        type_kind = filtered[0].type.kind
        if isinstance(type_kind, _IdlTypeDefTyStruct):
            return f"types.{type_kind.name}(**{prefix}{field.name})"
        return f"{prefix}{field.name}"
    if isinstance(field_type, _IdlTypeOption):
        initializer = struct_field_initializer(
            idl, _IdlField(field.name, field_type.option), prefix
        )
        # skip coercion when not needed
        if initializer == f"{prefix}{field.name}":
            return initializer
        return f"({prefix}{field.name} and {initializer}) or None"
    if isinstance(field_type, _IdlTypeCOption):
        initializer = struct_field_initializer(
            idl, _IdlField(field.name, field_type.coption), prefix
        )
        # skip coercion when not needed
        if initializer == f"{prefix}{field.name}":
            return initializer
        return f"({prefix}{field.name} and {initializer}) or None"
    if isinstance(field_type, _IdlTypeArray):
        map_body = struct_field_initializer(
            idl, _IdlField("item", field_type.array[0]), ""
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{prefix}{field.name}"
        return f"list(map(lambda item: {map_body}, {prefix}{field.name}))"
    if isinstance(field_type, _IdlTypeVec):
        map_body = struct_field_initializer(idl, _IdlField("item", field_type.vec), "")
        # skip mapping when not needed
        if map_body == "item":
            return f"{prefix}{field.name}"
        return f"list(map(lambda item: {map_body}, {prefix}{field.name}))"
    raise ValueError(f"Unrecognized type: {field_type}")

def field_to_json(idl: Idl, ty: _IdlField, val_prefix: str = "") -> str:
    ty_type = ty.type
    if ty_type in {
        "bool",
        "u8",
        "i8",
        "u16",
        "i16",
        "u32",
        "i32",
        "f32",
        "u64",
        "i64",
        "f64",
        "u128",
        "i128",
        "string",
        "bytes",
    }:
        return f"{val_prefix}{ty.name}"
    if ty_type == "publicKey":
        return f"{val_prefix}{ty.name}.to_base58()"
    if isinstance(ty_type, _IdlTypeVec):
        map_body = field_to_json(idl, _IdlField("item", ty_type.vec))
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty.name}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty.name}))"
    if isinstance(ty_type, _IdlTypeArray):
        map_body = field_to_json(idl, _IdlField("item", ty_type.array[0]))
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty.name}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty.name}))"
    if isinstance(ty_type, _IdlTypeOption):
        value = field_to_json(idl, _IdlField(ty.name, ty_type.option), val_prefix)
        # skip coercion when not needed
        if value == f"{val_prefix}{ty.name}":
            return value
        return f"({val_prefix}{ty.name} and {value}) or None"
    if isinstance(ty_type, _IdlTypeCOption):
        value = field_to_json(idl, _IdlField(ty.name, ty_type.coption), val_prefix)
        # skip coercion when not needed
        if value == f"{val_prefix}{ty.name}":
            return value
        return f"({val_prefix}{ty.name} and {value}) or None"
    if isinstance(ty_type, _IdlTypeDefined):
        defined = ty_type.defined
        filtered = [t for t in idl.types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        return f"{val_prefix}{ty.name}.to_json()"
    raise ValueError(f"Unrecognized type: {ty_type}")

def idl_type_to_json_type(ty: _IdlType, defined_types_prefix: str = "types.") -> str:
    if ty == "bool":
        return "bool"
    if ty in {"u8", "i8", "u16", "u16" "u32", "i32", "u64", "i64", "u128", "i128"}:
        return "int"
    if ty in {"f32", "f64"}:
        return "float"
    if ty in {"string", "bytes", "publicKey"}:
        return "str"
    if isinstance(ty, _IdlTypeVec):
        inner = idl_type_to_json_type(ty.vec, defined_types_prefix)
        return f"list[{inner}]"
    if isinstance(ty, _IdlTypeArray):
        inner = idl_type_to_json_type(ty.array[0], defined_types_prefix)
        return f"list[{inner}]"
    if isinstance(ty, _IdlTypeOption):
        inner = idl_type_to_json_type(ty.option, defined_types_prefix)
        return f"Optional[{inner}]"
    if isinstance(ty, _IdlTypeCOption):
        inner = idl_type_to_json_type(ty.coption, defined_types_prefix)
        return f"Optional[{inner}]"
    if isinstance(ty, _IdlTypeDefined):
        return f"{defined_types_prefix}{json_interface_name(ty.defined)}"
    raise ValueError(f"Unrecognized type: {ty}")
