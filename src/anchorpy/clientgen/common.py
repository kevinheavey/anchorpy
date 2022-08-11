"""Code generation utilities."""
from typing import Optional
import keyword
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

_DEFAULT_DEFINED_TYPES_PREFIX = "types."

INT_TYPES = {"u8", "i8", "u16", "i16", "u32", "i32", "u64", "i64", "u128", "i128"}
FLOAT_TYPES = {"f32", "f64"}
NUMBER_TYPES = INT_TYPES | FLOAT_TYPES


def _fields_interface_name(type_name: str) -> str:
    return f"{type_name}Fields"


def _value_interface_name(type_name: str) -> str:
    return f"{type_name}Value"


def _kind_interface_name(type_name: str) -> str:
    return f"{type_name}Kind"


def _json_interface_name(type_name: str) -> str:
    return f"{type_name}JSON"


def _sanitize(name: str) -> str:
    return f"{name}_" if keyword.iskeyword(name) else name


def _py_type_from_idl(
    idl: Idl,
    ty: _IdlType,
    types_relative_imports: bool,
    use_fields_interface_for_struct: bool,
) -> str:
    if isinstance(ty, _IdlTypeVec):
        inner_type = _py_type_from_idl(
            idl=idl,
            ty=ty.vec,
            types_relative_imports=types_relative_imports,
            use_fields_interface_for_struct=use_fields_interface_for_struct,
        )
        return f"list[{inner_type}]"
    if isinstance(ty, _IdlTypeOption):
        inner_type = _py_type_from_idl(
            idl=idl,
            ty=ty.option,
            types_relative_imports=types_relative_imports,
            use_fields_interface_for_struct=use_fields_interface_for_struct,
        )
        return f"typing.Optional[{inner_type}]"
    if isinstance(ty, _IdlTypeCOption):
        inner_type = _py_type_from_idl(
            idl=idl,
            ty=ty.coption,
            types_relative_imports=types_relative_imports,
            use_fields_interface_for_struct=use_fields_interface_for_struct,
        )
        return f"typing.Optional[{inner_type}]"
    if isinstance(ty, _IdlTypeDefined):
        defined = _sanitize(ty.defined)
        filtered = [t for t in idl.types if _sanitize(t.name) == defined]
        defined_types_prefix = (
            "" if types_relative_imports else _DEFAULT_DEFINED_TYPES_PREFIX
        )
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        typedef_type = filtered[0].type
        module = _sanitize(snake(ty.defined))
        if isinstance(typedef_type, _IdlTypeDefTyStruct):
            name = (
                _fields_interface_name(ty.defined)
                if use_fields_interface_for_struct
                else defined
            )
        else:
            # enum
            name = _kind_interface_name(ty.defined)
        return f"{defined_types_prefix}{module}.{name}"
    if isinstance(ty, _IdlTypeArray):
        inner_type = _py_type_from_idl(
            idl=idl,
            ty=ty.array[0],
            types_relative_imports=types_relative_imports,
            use_fields_interface_for_struct=use_fields_interface_for_struct,
        )
        return f"list[{inner_type}]"
    if ty in {"bool", "bytes"}:
        return ty
    if ty in INT_TYPES:
        return "int"
    if ty in FLOAT_TYPES:
        return "float"
    if ty == "string":
        return "str"
    if ty == "publicKey":
        return "PublicKey"
    raise ValueError(f"Unrecognized type: {ty}")


def _layout_for_type(
    idl: Idl,
    ty: _IdlType,
    types_relative_imports: bool,
    name: Optional[str] = None,
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
        layout = _layout_for_type(
            idl=idl, ty=ty.vec, types_relative_imports=types_relative_imports
        )
        cast_layout = f"typing.cast(Construct, {layout})"
        inner = f"borsh.Vec({cast_layout})"
    elif isinstance(ty, _IdlTypeOption):
        layout = _layout_for_type(
            idl=idl, ty=ty.option, types_relative_imports=types_relative_imports
        )
        inner = f"borsh.Option({layout})"
    elif isinstance(ty, _IdlTypeCOption):
        layout = _layout_for_type(
            idl=idl, ty=ty.coption, types_relative_imports=types_relative_imports
        )
        inner = f"COption({layout})"
    elif isinstance(ty, _IdlTypeDefined):
        defined = _sanitize(ty.defined)
        filtered = [t for t in idl.types if _sanitize(t.name) == defined]
        typedef_type = filtered[0].type
        defined_types_prefix = (
            "" if types_relative_imports else _DEFAULT_DEFINED_TYPES_PREFIX
        )
        module = snake(defined)
        inner = (
            f"{defined_types_prefix}{module}.{defined}.layout"
            if isinstance(typedef_type, _IdlTypeDefTyStruct)
            else f"{defined_types_prefix}{module}.layout"
        )
    elif isinstance(ty, _IdlTypeArray):
        layout = _layout_for_type(
            idl=idl, ty=ty.array[0], types_relative_imports=types_relative_imports
        )
        inner = f"{layout}[{ty.array[1]}]"
    else:
        raise ValueError(f"Unrecognized type: {ty}")

    if name is None:
        return inner
    return f'"{name}" / {inner}'


def _maybe_none(to_check: str, if_not_none: str) -> str:
    return f"(None if {to_check} is None else {if_not_none})"


def _field_to_encodable(
    idl: Idl,
    ty: _IdlField,
    types_relative_imports: bool,
    val_prefix: str = "",
    val_suffix: str = "",
) -> str:
    ty_type = ty.type
    ty_name = _sanitize(ty.name)
    if isinstance(ty_type, _IdlTypeVec):
        map_body = _field_to_encodable(
            idl=idl,
            ty=_IdlField("item", ty_type.vec),
            val_prefix="",
            types_relative_imports=types_relative_imports,
            val_suffix="",
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty_name}{val_suffix}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty_name}{val_suffix}))"
    if isinstance(ty_type, _IdlTypeOption):
        encodable = _field_to_encodable(
            idl=idl,
            ty=_IdlField(ty_name, ty_type.option),
            val_prefix=val_prefix,
            types_relative_imports=types_relative_imports,
            val_suffix=val_suffix,
        )
        if encodable == f"{val_prefix}{ty_name}{val_suffix}":
            return encodable
        return _maybe_none(f"{val_prefix}{ty_name}{val_suffix}", encodable)
    if isinstance(ty_type, _IdlTypeCOption):
        raise NotImplementedError("COption not implemented.")
    if isinstance(ty_type, _IdlTypeDefined):
        defined = _sanitize(ty_type.defined)
        filtered = [t for t in idl.types if _sanitize(t.name) == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        typedef_type = filtered[0].type
        if isinstance(typedef_type, _IdlTypeDefTyStruct):
            val_full_name = f"{val_prefix}{ty_name}{val_suffix}"
            return f"{val_full_name}.to_encodable()"
        return f"{val_prefix}{ty_name}{val_suffix}.to_encodable()"
    if isinstance(ty_type, _IdlTypeArray):
        map_body = _field_to_encodable(
            idl=idl,
            ty=_IdlField("item", ty_type.array[0]),
            val_prefix="",
            types_relative_imports=types_relative_imports,
            val_suffix="",
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty_name}{val_suffix}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty_name}{val_suffix}))"
    if ty_type in {
        "bool",
        *NUMBER_TYPES,
        "string",
        "publicKey",
        "bytes",
    }:
        return f"{val_prefix}{ty_name}{val_suffix}"
    raise ValueError(f"Unrecognized type: {ty_type}")


def _field_from_decoded(
    idl: Idl, ty: _IdlField, types_relative_imports: bool, val_prefix: str = ""
) -> str:
    ty_type = ty.type
    ty_name = _sanitize(ty.name)
    if isinstance(ty_type, _IdlTypeVec):
        map_body = _field_from_decoded(
            idl=idl,
            ty=_IdlField("item", ty_type.vec),
            val_prefix="",
            types_relative_imports=types_relative_imports,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty_name}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty_name}))"
    if isinstance(ty_type, _IdlTypeOption):
        decoded = _field_from_decoded(
            idl=idl,
            ty=_IdlField(ty_name, ty_type.option),
            types_relative_imports=types_relative_imports,
            val_prefix=val_prefix,
        )
        # skip coercion when not needed
        if decoded == f"{val_prefix}{ty_name}":
            return decoded
        return _maybe_none(f"{val_prefix}{ty_name}", decoded)
    if isinstance(ty_type, _IdlTypeCOption):
        raise NotImplementedError("COption not implemented.")
    if isinstance(ty_type, _IdlTypeDefined):
        defined = _sanitize(ty_type.defined)
        filtered = [t for t in idl.types if _sanitize(t.name) == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        typedef_type = filtered[0].type
        from_decoded_func_path = (
            f"{snake(defined)}.{defined}"
            if isinstance(typedef_type, _IdlTypeDefTyStruct)
            else f"{snake(defined)}"
        )
        defined_types_prefix = (
            "" if types_relative_imports else _DEFAULT_DEFINED_TYPES_PREFIX
        )
        full_func_path = f"{defined_types_prefix}{from_decoded_func_path}"
        from_decoded_arg = f"{val_prefix}{ty_name}"
        return f"{full_func_path}.from_decoded({from_decoded_arg})"
    if isinstance(ty_type, _IdlTypeArray):
        map_body = _field_from_decoded(
            idl=idl,
            ty=_IdlField("item", ty_type.array[0]),
            val_prefix="",
            types_relative_imports=types_relative_imports,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty_name}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty_name}))"
    if ty_type in {
        "bool",
        *NUMBER_TYPES,
        "string",
        "publicKey",
        "bytes",
    }:
        return f"{val_prefix}{ty_name}"
    raise ValueError(f"Unrecognized type: {ty_type}")


def _struct_field_initializer(
    idl: Idl,
    field: _IdlField,
    types_relative_imports: bool,
    prefix: str = 'fields["',
    suffix: str = '"]',
) -> str:
    field_type = field.type
    field_name = _sanitize(field.name)
    if isinstance(field_type, _IdlTypeDefined):
        defined = _sanitize(field_type.defined)
        filtered = [t for t in idl.types if _sanitize(t.name) == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        typedef_type = filtered[0].type
        if isinstance(typedef_type, _IdlTypeDefTyStruct):
            module = snake(defined)
            defined_types_prefix = (
                "" if types_relative_imports else _DEFAULT_DEFINED_TYPES_PREFIX
            )
            obj_name = f"{defined_types_prefix}{module}.{defined}"
            return f"{obj_name}(**{prefix}{field_name}{suffix})"
        return f"{prefix}{field_name}{suffix}"
    if isinstance(field_type, _IdlTypeOption):
        initializer = _struct_field_initializer(
            idl=idl,
            field=_IdlField(field_name, field_type.option),
            prefix=prefix,
            suffix=suffix,
            types_relative_imports=types_relative_imports,
        )
        # skip coercion when not needed
        if initializer == f"{prefix}{field_name}{suffix}":
            return initializer
        return _maybe_none(f"{prefix}{field_name}{suffix}", initializer)
    if isinstance(field_type, _IdlTypeCOption):
        initializer = _struct_field_initializer(
            idl=idl,
            field=_IdlField(field_name, field_type.coption),
            prefix=prefix,
            suffix=suffix,
            types_relative_imports=types_relative_imports,
        )
        # skip coercion when not needed
        if initializer == f"{prefix}{field_name}{suffix}":
            return initializer
        return _maybe_none(f"{prefix}{field_name}", initializer)
    if isinstance(field_type, _IdlTypeArray):
        map_body = _struct_field_initializer(
            idl=idl,
            field=_IdlField("item", field_type.array[0]),
            prefix="",
            suffix="",
            types_relative_imports=types_relative_imports,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{prefix}{field_name}{suffix}"
        return f"list(map(lambda item: {map_body}, {prefix}{field_name}{suffix}))"
    if isinstance(field_type, _IdlTypeVec):
        map_body = _struct_field_initializer(
            idl=idl,
            field=_IdlField("item", field_type.vec),
            prefix="",
            suffix="",
            types_relative_imports=types_relative_imports,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{prefix}{field_name}{suffix}"
        return f"list(map(lambda item: {map_body}, {prefix}{field_name}{suffix}))"
    if field_type in {
        "bool",
        *NUMBER_TYPES,
        "string",
        "publicKey",
        "bytes",
    }:
        return f"{prefix}{field_name}{suffix}"
    raise ValueError(f"Unrecognized type: {field_type}")


def _field_to_json(
    idl: Idl, ty: _IdlField, val_prefix: str = "", val_suffix: str = ""
) -> str:
    ty_type = ty.type
    var_name = f"{val_prefix}{ty.name}{val_suffix}"
    if ty_type == "publicKey":
        return f"str({var_name})"
    if isinstance(ty_type, _IdlTypeVec):
        map_body = _field_to_json(idl, _IdlField("item", ty_type.vec))
        # skip mapping when not needed
        if map_body == "item":
            return var_name
        return f"list(map(lambda item: {map_body}, {var_name}))"
    if isinstance(ty_type, _IdlTypeArray):
        map_body = _field_to_json(idl, _IdlField("item", ty_type.array[0]))
        # skip mapping when not needed
        if map_body == "item":
            return var_name
        return f"list(map(lambda item: {map_body}, {var_name}))"
    if isinstance(ty_type, _IdlTypeOption):
        value = _field_to_json(
            idl, _IdlField(ty.name, ty_type.option), val_prefix, val_suffix
        )
        # skip coercion when not needed
        if value == var_name:
            return value
        return _maybe_none(var_name, value)
    if isinstance(ty_type, _IdlTypeCOption):
        value = _field_to_json(
            idl, _IdlField(ty.name, ty_type.coption), val_prefix, val_suffix
        )
        # skip coercion when not needed
        if value == var_name:
            return value
        return _maybe_none(var_name, value)
    if isinstance(ty_type, _IdlTypeDefined):
        defined = ty_type.defined
        filtered = [t for t in idl.types if t.name == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        return f"{var_name}.to_json()"
    if ty_type == "bytes":
        return f"list({var_name})"
    if ty_type in {
        "bool",
        *NUMBER_TYPES,
        "string",
    }:
        return var_name
    raise ValueError(f"Unrecognized type: {ty_type}")


def _idl_type_to_json_type(ty: _IdlType, types_relative_imports: bool) -> str:
    if isinstance(ty, _IdlTypeVec):
        inner = _idl_type_to_json_type(
            ty=ty.vec, types_relative_imports=types_relative_imports
        )
        return f"list[{inner}]"
    if isinstance(ty, _IdlTypeArray):
        inner = _idl_type_to_json_type(
            ty=ty.array[0], types_relative_imports=types_relative_imports
        )
        return f"list[{inner}]"
    if isinstance(ty, _IdlTypeOption):
        inner = _idl_type_to_json_type(
            ty=ty.option, types_relative_imports=types_relative_imports
        )
        return f"typing.Optional[{inner}]"
    if isinstance(ty, _IdlTypeCOption):
        inner = _idl_type_to_json_type(
            ty=ty.coption, types_relative_imports=types_relative_imports
        )
        return f"typing.Optional[{inner}]"
    if isinstance(ty, _IdlTypeDefined):
        defined_types_prefix = (
            "" if types_relative_imports else _DEFAULT_DEFINED_TYPES_PREFIX
        )
        module = _sanitize(snake(ty.defined))
        return f"{defined_types_prefix}{module}.{_json_interface_name(ty.defined)}"
    if ty == "bool":
        return "bool"
    if ty in INT_TYPES:
        return "int"
    if ty in FLOAT_TYPES:
        return "float"
    if ty == "bytes":
        return "list[int]"
    if ty in {"string", "publicKey"}:
        return "str"
    raise ValueError(f"Unrecognized type: {ty}")


def _field_from_json(
    idl: Idl,
    ty: _IdlField,
    types_relative_imports: bool,
    param_prefix: str = 'obj["',
    param_suffix: str = '"]',
) -> str:
    ty_type = ty.type
    ty_name = _sanitize(ty.name)
    var_name = f"{param_prefix}{ty.name}{param_suffix}"
    if ty_type == "publicKey":
        return f"PublicKey({var_name})"
    if isinstance(ty_type, _IdlTypeVec):
        map_body = _field_from_json(
            idl=idl,
            ty=_IdlField("item", ty_type.vec),
            param_prefix="",
            param_suffix="",
            types_relative_imports=types_relative_imports,
        )
        # skip mapping when not needed
        if map_body == "item":
            return var_name
        return f"list(map(lambda item: {map_body}, {var_name}))"
    if isinstance(ty_type, _IdlTypeArray):
        map_body = _field_from_json(
            idl=idl,
            ty=_IdlField("item", ty_type.array[0]),
            param_prefix="",
            param_suffix="",
            types_relative_imports=types_relative_imports,
        )
        # skip mapping when not needed
        if map_body == "item":
            return var_name
        return f"list(map(lambda item: {map_body}, {var_name}))"
    if isinstance(ty_type, _IdlTypeOption):
        inner = _field_from_json(
            idl=idl,
            ty=_IdlField(ty_name, ty_type.option),
            param_prefix=param_prefix,
            param_suffix=param_suffix,
            types_relative_imports=types_relative_imports,
        )
        # skip coercion when not needed
        if inner == var_name:
            return inner
        return _maybe_none(var_name, inner)
    if isinstance(ty_type, _IdlTypeCOption):
        inner = _field_from_json(
            idl=idl,
            ty=_IdlField(ty_name, ty_type.coption),
            param_prefix=param_prefix,
            param_suffix=param_suffix,
            types_relative_imports=types_relative_imports,
        )
        # skip coercion when not needed
        if inner == var_name:
            return inner
        return _maybe_none(var_name, inner)
    if isinstance(ty_type, _IdlTypeDefined):
        from_json_arg = var_name
        defined = _sanitize(ty_type.defined)
        defined_snake = _sanitize(snake(ty_type.defined))
        filtered = [t for t in idl.types if _sanitize(t.name) == defined]
        typedef_type = filtered[0].type
        from_json_func_path = (
            f"{defined_snake}.{defined}"
            if isinstance(typedef_type, _IdlTypeDefTyStruct)
            else f"{defined_snake}"
        )
        defined_types_prefix = (
            "" if types_relative_imports else _DEFAULT_DEFINED_TYPES_PREFIX
        )
        full_func_path = f"{defined_types_prefix}{from_json_func_path}"
        return f"{full_func_path}.from_json({from_json_arg})"
    if ty_type == "bytes":
        return f"bytes({var_name})"
    if ty_type in {
        "bool",
        *NUMBER_TYPES,
        "string",
    }:
        return var_name
    raise ValueError(f"Unrecognized type: {ty_type}")
