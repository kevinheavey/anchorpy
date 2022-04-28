"""Code generation utilities."""
from typing import Optional
from pyheck import snake
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


def _fields_interface_name(type_name: str) -> str:
    return f"{type_name}Fields"


def _value_interface_name(type_name: str) -> str:
    return f"{type_name}Value"


def _kind_interface_name(type_name: str) -> str:
    return f"{type_name}Kind"


def _json_interface_name(type_name: str) -> str:
    return f"{type_name}JSON"


def _py_type_from_idl(
    idl: Idl,
    ty: _IdlType,
    defined_types_prefix: str = "types.",
    use_fields_interface_for_struct: bool = True,
) -> str:
    if isinstance(ty, _IdlTypeVec):
        inner_type = _py_type_from_idl(
            idl=idl,
            ty=ty.vec,
            defined_types_prefix=defined_types_prefix,
            use_fields_interface_for_struct=use_fields_interface_for_struct,
        )
        return f"list[{inner_type}]"
    elif isinstance(ty, _IdlTypeOption):
        inner_type = _py_type_from_idl(
            idl=idl,
            ty=ty.option,
            defined_types_prefix=defined_types_prefix,
            use_fields_interface_for_struct=use_fields_interface_for_struct,
        )
        return f"typing.Optional[{inner_type}]"
    elif isinstance(ty, _IdlTypeCOption):
        inner_type = _py_type_from_idl(
            idl=idl,
            ty=ty.coption,
            defined_types_prefix=defined_types_prefix,
            use_fields_interface_for_struct=use_fields_interface_for_struct,
        )
        return f"typing.Optional[{inner_type}]"
    elif isinstance(ty, _IdlTypeDefined):
        defined = ty.defined
        filtered = [t for t in idl.types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        type_kind = filtered[0].type.kind
        if isinstance(type_kind, _IdlTypeDefTyStruct):
            name = (
                _fields_interface_name(ty.defined)
                if use_fields_interface_for_struct
                else ty.defined
            )
            return f"{defined_types_prefix}{name}"
        name = _kind_interface_name(ty.defined)
        return f"{defined_types_prefix}{name}"
    elif isinstance(ty, _IdlTypeArray):
        inner_type = _py_type_from_idl(
            idl=idl,
            ty=ty.array[0],
            defined_types_prefix=defined_types_prefix,
            use_fields_interface_for_struct=use_fields_interface_for_struct,
        )
        return f"list[{inner_type}]"
    elif ty == "bool":
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
    raise ValueError(f"Unrecognized type: {ty}")


def _layout_for_type(
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
        inner = "BorshPubkey"
    elif isinstance(ty, _IdlTypeVec):
        inner = f"borsh.Vec({_layout_for_type(ty=ty.vec)})"
    elif isinstance(ty, _IdlTypeOption):
        inner = f"borsh.Option({_layout_for_type(ty=ty.option)})"
    elif isinstance(ty, _IdlTypeCOption):
        inner = f"COption({_layout_for_type(ty=ty.coption)})"
    elif isinstance(ty, _IdlTypeDefined):
        inner = f"{defined_types_prefix}{snake(ty.defined)}.layout()"
    elif isinstance(ty, _IdlTypeArray):
        inner = f"{_layout_for_type(ty=ty.array[0])}[{ty.array[1]}]"
    else:
        raise ValueError(f"Unrecognized type: {ty}")

    if name is None:
        return inner
    return f'"{name}" / {inner}'


def _field_to_encodable(
    idl: Idl,
    ty: _IdlField,
    val_prefix: str = "",
    defined_types_prefix: str = "types.",
    val_suffix: str = "",
) -> str:
    ty_type = ty.type
    if isinstance(ty_type, _IdlTypeVec):
        map_body = _field_to_encodable(
            idl=idl,
            ty=_IdlField("item", ty_type.vec),
            val_prefix="",
            defined_types_prefix=defined_types_prefix,
            val_suffix=val_suffix,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty.name}{val_suffix}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty.name}{val_suffix}))"
    if isinstance(ty_type, _IdlTypeOption):
        encodable = _field_to_encodable(
            idl=idl,
            ty=_IdlField(ty.name, ty_type.option),
            val_prefix=val_prefix,
            defined_types_prefix=defined_types_prefix,
            val_suffix=val_suffix,
        )
        if encodable == f"{val_prefix}{ty.name}{val_suffix}":
            return encodable
        return f"({val_prefix}{ty.name}{val_suffix} and {encodable}) or None"
    if isinstance(ty_type, _IdlTypeCOption):
        raise NotImplementedError("COption not implemented.")
    if isinstance(ty_type, _IdlTypeDefined):
        defined = ty_type.defined
        filtered = [t for t in idl.types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        type_kind = filtered[0].type.kind
        if isinstance(type_kind, _IdlTypeDefTyStruct):
            val_full_name = f"{val_prefix}{ty.name}{val_suffix}"
            return f"{defined_types_prefix}{defined}.to_encodable({val_full_name})"
        return f"{val_prefix}{ty.name}{val_suffix}.to_encodable()"
    if isinstance(ty_type, _IdlTypeArray):
        map_body = _field_to_encodable(
            idl=idl,
            ty=_IdlField("item", ty_type.array[0]),
            val_prefix="",
            defined_types_prefix=defined_types_prefix,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty.name}{val_suffix}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty.name}{val_suffix}))"
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
        return f"{val_prefix}{ty.name}{val_suffix}"
    raise ValueError(f"Unrecognized type: {ty_type}")


def _field_from_decoded(
    idl: Idl, ty: _IdlField, val_prefix: str = "", defined_types_prefix: str = "types."
) -> str:
    ty_type = ty.type
    if isinstance(ty_type, _IdlTypeVec):
        map_body = _field_from_decoded(
            idl=idl,
            ty=_IdlField("item", ty_type.vec),
            val_prefix="",
            defined_types_prefix=defined_types_prefix,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty.name}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty.name}))"
    if isinstance(ty_type, _IdlTypeOption):
        decoded = _field_from_decoded(
            idl=idl, ty=_IdlField(ty.name, ty_type.option), val_prefix=val_prefix
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
        return f"{defined_types_prefix}{defined}.from_decoded({val_prefix}{ty.name})"
    if isinstance(ty_type, _IdlTypeArray):
        map_body = _field_from_decoded(
            idl=idl,
            ty=_IdlField("item", ty_type.array[0]),
            val_prefix="",
            defined_types_prefix=defined_types_prefix,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty.name}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty.name}))"
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
    raise ValueError(f"Unrecognized type: {ty_type}")


def _struct_field_initializer(
    idl: Idl,
    field: _IdlField,
    prefix: str = 'fields["',
    suffix: str = '"]',
    defined_types_prefix: str = "types.",
) -> str:
    field_type = field.type
    if isinstance(field_type, _IdlTypeDefined):
        defined = field_type.defined
        filtered = [t for t in idl.types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        type_kind = filtered[0].type.kind
        if isinstance(type_kind, _IdlTypeDefTyStruct):
            obj_name = f"{defined_types_prefix}{type_kind.name}"
            return f"{obj_name}(**{prefix}{field.name}{suffix})"
        return f"{prefix}{field.name}{suffix}"
    if isinstance(field_type, _IdlTypeOption):
        initializer = _struct_field_initializer(
            idl=idl,
            field=_IdlField(field.name, field_type.option),
            prefix=prefix,
            suffix=suffix,
        )
        # skip coercion when not needed
        if initializer == f"{prefix}{field.name}{suffix}":
            return initializer
        return f"({prefix}{field.name}{suffix} and {initializer}) or None"
    if isinstance(field_type, _IdlTypeCOption):
        initializer = _struct_field_initializer(
            idl=idl,
            field=_IdlField(field.name, field_type.coption),
            prefix=prefix,
            suffix=suffix,
        )
        # skip coercion when not needed
        if initializer == f"{prefix}{field.name}{suffix}":
            return initializer
        return f"({prefix}{field.name} and {initializer}) or None"
    if isinstance(field_type, _IdlTypeArray):
        map_body = _struct_field_initializer(
            idl=idl, field=_IdlField("item", field_type.array[0]), prefix="", suffix=""
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{prefix}{field.name}{suffix}"
        return f"list(map(lambda item: {map_body}, {prefix}{field.name}{suffix}))"
    if isinstance(field_type, _IdlTypeVec):
        map_body = _struct_field_initializer(
            idl=idl, field=_IdlField("item", field_type.vec), prefix="", suffix=""
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{prefix}{field.name}{suffix}"
        return f"list(map(lambda item: {map_body}, {prefix}{field.name}{suffix}))"
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
        return f"{prefix}{field.name}{suffix}"
    raise ValueError(f"Unrecognized type: {field_type}")


def _field_to_json(
    idl: Idl, ty: _IdlField, val_prefix: str = "", val_suffix: str = ""
) -> str:
    ty_type = ty.type
    if ty_type == "publicKey":
        return f"str({val_prefix}{ty.name}{val_suffix})"
    if isinstance(ty_type, _IdlTypeVec):
        map_body = _field_to_json(idl, _IdlField("item", ty_type.vec))
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty.name}{val_suffix}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty.name}{val_suffix}))"
    if isinstance(ty_type, _IdlTypeArray):
        map_body = _field_to_json(idl, _IdlField("item", ty_type.array[0]))
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty.name}{val_suffix}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty.name}{val_suffix}))"
    if isinstance(ty_type, _IdlTypeOption):
        value = _field_to_json(
            idl, _IdlField(ty.name, ty_type.option), val_prefix, val_suffix
        )
        # skip coercion when not needed
        if value == f"{val_prefix}{ty.name}{val_suffix}":
            return value
        return f"({val_prefix}{ty.name}{val_suffix} and {value}) or None"
    if isinstance(ty_type, _IdlTypeCOption):
        value = _field_to_json(
            idl, _IdlField(ty.name, ty_type.coption), val_prefix, val_suffix
        )
        # skip coercion when not needed
        if value == f"{val_prefix}{ty.name}{val_suffix}":
            return value
        return f"({val_prefix}{ty.name}{val_suffix} and {value}) or None"
    if isinstance(ty_type, _IdlTypeDefined):
        defined = ty_type.defined
        filtered = [t for t in idl.types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        return f"{val_prefix}{ty.name}{val_suffix}.to_json()"
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
        return f"{val_prefix}{ty.name}{val_suffix}"
    raise ValueError(f"Unrecognized type: {ty_type}")


def _idl_type_to_json_type(ty: _IdlType, defined_types_prefix: str = "types.") -> str:
    if isinstance(ty, _IdlTypeVec):
        inner = _idl_type_to_json_type(
            ty=ty.vec, defined_types_prefix=defined_types_prefix
        )
        return f"list[{inner}]"
    if isinstance(ty, _IdlTypeArray):
        inner = _idl_type_to_json_type(
            ty=ty.array[0], defined_types_prefix=defined_types_prefix
        )
        return f"list[{inner}]"
    if isinstance(ty, _IdlTypeOption):
        inner = _idl_type_to_json_type(
            ty=ty.option, defined_types_prefix=defined_types_prefix
        )
        return f"typing.Optional[{inner}]"
    if isinstance(ty, _IdlTypeCOption):
        inner = _idl_type_to_json_type(
            ty=ty.coption, defined_types_prefix=defined_types_prefix
        )
        return f"typing.Optional[{inner}]"
    if isinstance(ty, _IdlTypeDefined):
        return f"{defined_types_prefix}{_json_interface_name(ty.defined)}"
    if ty == "bool":
        return "bool"
    if ty in {"u8", "i8", "u16", "u16" "u32", "i32", "u64", "i64", "u128", "i128"}:
        return "int"
    if ty in {"f32", "f64"}:
        return "float"
    if ty in {"string", "bytes", "publicKey"}:
        return "str"
    raise ValueError(f"Unrecognized type: {ty}")


def _field_from_json(
    ty: _IdlField, json_param_name: str = "obj", defined_types_prefix: str = "types."
) -> str:
    param_prefix = json_param_name + '["' if json_param_name else ""
    param_suffix = '"]' if json_param_name else ""
    ty_type = ty.type
    if ty_type == "publicKey":
        return f"PublicKey({param_prefix}{ty.name}{param_suffix})"
    if isinstance(ty_type, _IdlTypeVec):
        map_body = _field_from_json(
            ty=_IdlField("item", ty_type.vec),
            json_param_name="",
            defined_types_prefix=defined_types_prefix,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{param_prefix}{ty.name}{param_suffix}"
        return (
            f"list(map(lambda item: {map_body}, {param_prefix}{ty.name}{param_suffix}))"
        )
    if isinstance(ty_type, _IdlTypeArray):
        map_body = _field_from_json(
            ty=_IdlField("item", ty_type.array[0]),
            json_param_name="",
            defined_types_prefix=defined_types_prefix,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{param_prefix}{ty.name}{param_suffix}"
        return (
            f"list(map(lambda item: {map_body}, {param_prefix}{ty.name}{param_suffix}))"
        )
    if isinstance(ty_type, _IdlTypeOption):
        inner = _field_from_json(
            ty=_IdlField(ty.name, ty_type.option),
            json_param_name=json_param_name,
            defined_types_prefix=defined_types_prefix,
        )
        # skip coercion when not needed
        if inner == f"{param_prefix}{ty.name}{param_suffix}":
            return inner
        return f"({param_prefix}{ty.name}{param_suffix} and {inner}) or None"
    if isinstance(ty_type, _IdlTypeCOption):
        inner = _field_from_json(
            ty=_IdlField(ty.name, ty_type.coption),
            json_param_name=json_param_name,
            defined_types_prefix=defined_types_prefix,
        )
        # skip coercion when not needed
        if inner == f"{param_prefix}{ty.name}{param_suffix}":
            return inner
        return f"({param_prefix}{ty.name}{param_suffix} and {inner}) or None"
    if isinstance(ty_type, _IdlTypeDefined):
        from_json_arg = f"{param_prefix}{ty.name}{param_suffix}"
        return f"{defined_types_prefix}{ty.name}.from_json({from_json_arg})"
    if ty_type in {
        "bool",
        "u8",
        "i8",
        "u16",
        "i16",
        "u32",
        "i32",
        "u64",
        "i64",
        "u128",
        "i128",
        "f32",
        "f64",
        "string",
        "bytes",
    }:
        return f"{param_prefix}{ty.name}{param_suffix}"
    raise ValueError(f"Unrecognized type: {ty_type}")
