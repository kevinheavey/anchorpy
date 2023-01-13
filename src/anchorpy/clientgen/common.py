"""Code generation utilities."""
import keyword
from typing import Optional

from anchorpy_core.idl import (
    Idl,
    IdlField,
    IdlType,
    IdlTypeArray,
    IdlTypeDefined,
    IdlTypeDefinitionTyStruct,
    IdlTypeOption,
    IdlTypeSimple,
    IdlTypeVec,
)
from pyheck import snake

_DEFAULT_DEFINED_TYPES_PREFIX = "types."

INT_TYPES = {
    IdlTypeSimple.U8,
    IdlTypeSimple.I8,
    IdlTypeSimple.U16,
    IdlTypeSimple.I16,
    IdlTypeSimple.U32,
    IdlTypeSimple.I32,
    IdlTypeSimple.U64,
    IdlTypeSimple.I64,
    IdlTypeSimple.U128,
    IdlTypeSimple.I128,
}
FLOAT_TYPES = {IdlTypeSimple.F32, IdlTypeSimple.F64}
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
    ty: IdlType,
    types_relative_imports: bool,
    use_fields_interface_for_struct: bool,
) -> str:
    if isinstance(ty, IdlTypeVec):
        inner_type = _py_type_from_idl(
            idl=idl,
            ty=ty.vec,
            types_relative_imports=types_relative_imports,
            use_fields_interface_for_struct=use_fields_interface_for_struct,
        )
        return f"list[{inner_type}]"
    if isinstance(ty, IdlTypeOption):
        inner_type = _py_type_from_idl(
            idl=idl,
            ty=ty.option,
            types_relative_imports=types_relative_imports,
            use_fields_interface_for_struct=use_fields_interface_for_struct,
        )
        return f"typing.Optional[{inner_type}]"
    if isinstance(ty, IdlTypeDefined):
        defined = _sanitize(ty.defined)
        filtered = [t for t in idl.types if _sanitize(t.name) == defined]
        maybe_coption_split = defined.split("COption<")
        if len(maybe_coption_split) == 2:
            inner_type = {"u64": "int", "Pubkey": "Pubkey"}[maybe_coption_split[1][:-1]]
            return f"typing.Optional[{inner_type}]"
        if defined == "&'astr":
            return "str"
        defined_types_prefix = (
            "" if types_relative_imports else _DEFAULT_DEFINED_TYPES_PREFIX
        )
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        typedef_type = filtered[0].ty
        module = _sanitize(snake(ty.defined))
        if isinstance(typedef_type, IdlTypeDefinitionTyStruct):
            name = (
                _fields_interface_name(ty.defined)
                if use_fields_interface_for_struct
                else defined
            )
        else:
            # enum
            name = _kind_interface_name(ty.defined)
        return f"{defined_types_prefix}{module}.{name}"
    if isinstance(ty, IdlTypeArray):
        inner_type = _py_type_from_idl(
            idl=idl,
            ty=ty.array[0],
            types_relative_imports=types_relative_imports,
            use_fields_interface_for_struct=use_fields_interface_for_struct,
        )
        return f"list[{inner_type}]"
    if ty in {IdlTypeSimple.Bool, IdlTypeSimple.Bytes}:
        return str(ty).replace("IdlTypeSimple.", "").lower()
    if ty in INT_TYPES:
        return "int"
    if ty in FLOAT_TYPES:
        return "float"
    if ty == IdlTypeSimple.String:
        return "str"
    if ty == IdlTypeSimple.PublicKey:
        return "Pubkey"
    raise ValueError(f"Unrecognized type: {ty}")


def _layout_for_type(
    idl: Idl,
    ty: IdlType,
    types_relative_imports: bool,
    name: Optional[str] = None,
) -> str:
    if ty == IdlTypeSimple.PublicKey:
        inner = "BorshPubkey"
    elif isinstance(ty, IdlTypeSimple):
        inner = str(ty).replace("IdlTypeSimple", "borsh")
    elif isinstance(ty, IdlTypeVec):
        layout = _layout_for_type(
            idl=idl, ty=ty.vec, types_relative_imports=types_relative_imports
        )
        cast_layout = f"typing.cast(Construct, {layout})"
        inner = f"borsh.Vec({cast_layout})"
    elif isinstance(ty, IdlTypeOption):
        layout = _layout_for_type(
            idl=idl, ty=ty.option, types_relative_imports=types_relative_imports
        )
        inner = f"borsh.Option({layout})"
    elif isinstance(ty, IdlTypeDefined):
        defined = _sanitize(ty.defined)
        maybe_coption_split = defined.split("COption<")
        if len(maybe_coption_split) == 2:
            layout_str = maybe_coption_split[1][:-1]
            layout = {"u64": "borsh.U64", "Pubkey": "BorshPubkey"}[layout_str]
            inner = f"COption({layout})"
        elif defined == "&'astr":
            return "borsh.String"
        else:
            filtered = [t for t in idl.types if _sanitize(t.name) == defined]
            typedef_type = filtered[0].ty
            defined_types_prefix = (
                "" if types_relative_imports else _DEFAULT_DEFINED_TYPES_PREFIX
            )
            module = snake(defined)
            inner = (
                f"{defined_types_prefix}{module}.{defined}.layout"
                if isinstance(typedef_type, IdlTypeDefinitionTyStruct)
                else f"{defined_types_prefix}{module}.layout"
            )
    elif isinstance(ty, IdlTypeArray):
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
    ty: IdlField,
    types_relative_imports: bool,
    val_prefix: str = "",
    val_suffix: str = "",
    convert_case: bool = True,
) -> str:
    ty_type = ty.ty
    maybe_converted = snake(ty.name) if convert_case else ty.name
    ty_name = _sanitize(maybe_converted)
    if isinstance(ty_type, IdlTypeVec):
        map_body = _field_to_encodable(
            idl=idl,
            ty=IdlField("item", docs=None, ty=ty_type.vec),
            val_prefix="",
            types_relative_imports=types_relative_imports,
            val_suffix="",
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty_name}{val_suffix}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty_name}{val_suffix}))"
    if isinstance(ty_type, IdlTypeOption):
        encodable = _field_to_encodable(
            idl=idl,
            ty=IdlField(ty_name, docs=None, ty=ty_type.option),
            val_prefix=val_prefix,
            types_relative_imports=types_relative_imports,
            val_suffix=val_suffix,
            convert_case=convert_case,
        )
        if encodable == f"{val_prefix}{ty_name}{val_suffix}":
            return encodable
        return _maybe_none(f"{val_prefix}{ty_name}{val_suffix}", encodable)
    if isinstance(ty_type, IdlTypeDefined):
        defined = _sanitize(ty_type.defined)
        maybe_coption_split = defined.split("COption<")
        if len(maybe_coption_split) == 2:
            inner_type = maybe_coption_split[1][:-1]
            encodable = _field_to_encodable(
                idl=idl,
                ty=IdlField(
                    ty_name,
                    docs=None,
                    ty={"u64": IdlTypeSimple.U64, "Pubkey": IdlTypeSimple.PublicKey}[
                        inner_type
                    ],
                ),
                val_prefix=val_prefix,
                types_relative_imports=types_relative_imports,
                val_suffix=val_suffix,
                convert_case=convert_case,
            )
            if encodable == f"{val_prefix}{ty_name}{val_suffix}":
                return encodable
            return _maybe_none(f"{val_prefix}{ty_name}{val_suffix}", encodable)
        elif defined == "&'astr":
            return f"{val_prefix}{ty_name}{val_suffix}"
        filtered = [t for t in idl.types if _sanitize(t.name) == defined]

        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        typedef_type = filtered[0].ty
        if isinstance(typedef_type, IdlTypeDefinitionTyStruct):
            val_full_name = f"{val_prefix}{ty_name}{val_suffix}"
            return f"{val_full_name}.to_encodable()"
        return f"{val_prefix}{ty_name}{val_suffix}.to_encodable()"
    if isinstance(ty_type, IdlTypeArray):
        map_body = _field_to_encodable(
            idl=idl,
            ty=IdlField("item", docs=None, ty=ty_type.array[0]),
            val_prefix="",
            types_relative_imports=types_relative_imports,
            val_suffix="",
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty_name}{val_suffix}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty_name}{val_suffix}))"
    if ty_type in {
        IdlTypeSimple.Bool,
        *NUMBER_TYPES,
        IdlTypeSimple.String,
        IdlTypeSimple.PublicKey,
        IdlTypeSimple.Bytes,
    }:
        return f"{val_prefix}{ty_name}{val_suffix}"
    raise ValueError(f"Unrecognized type: {ty_type}")


def _field_from_decoded(
    idl: Idl, ty: IdlField, types_relative_imports: bool, val_prefix: str = ""
) -> str:
    ty_type = ty.ty
    ty_name = _sanitize(ty.name)
    if isinstance(ty_type, IdlTypeVec):
        map_body = _field_from_decoded(
            idl=idl,
            ty=IdlField("item", docs=None, ty=ty_type.vec),
            val_prefix="",
            types_relative_imports=types_relative_imports,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty_name}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty_name}))"
    if isinstance(ty_type, IdlTypeOption):
        decoded = _field_from_decoded(
            idl=idl,
            ty=IdlField(ty_name, docs=None, ty=ty_type.option),
            types_relative_imports=types_relative_imports,
            val_prefix=val_prefix,
        )
        # skip coercion when not needed
        if decoded == f"{val_prefix}{ty_name}":
            return decoded
        return _maybe_none(f"{val_prefix}{ty_name}", decoded)
    if isinstance(ty_type, IdlTypeDefined):
        defined = _sanitize(ty_type.defined)
        maybe_coption_split = defined.split("COption<")
        if len(maybe_coption_split) == 2:
            inner_type = maybe_coption_split[1][:-1]
            decoded = _field_from_decoded(
                idl=idl,
                ty=IdlField(
                    ty_name,
                    docs=None,
                    ty={"u64": IdlTypeSimple.U64, "Pubkey": IdlTypeSimple.PublicKey}[
                        inner_type
                    ],
                ),
                types_relative_imports=types_relative_imports,
                val_prefix=val_prefix,
            )
            # skip coercion when not needed
            if decoded == f"{val_prefix}{ty_name}":
                return decoded
            return _maybe_none(f"{val_prefix}{ty_name}", decoded)
        filtered = [t for t in idl.types if _sanitize(t.name) == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        typedef_type = filtered[0].ty
        from_decoded_func_path = (
            f"{snake(defined)}.{defined}"
            if isinstance(typedef_type, IdlTypeDefinitionTyStruct)
            else f"{snake(defined)}"
        )
        defined_types_prefix = (
            "" if types_relative_imports else _DEFAULT_DEFINED_TYPES_PREFIX
        )
        full_func_path = f"{defined_types_prefix}{from_decoded_func_path}"
        from_decoded_arg = f"{val_prefix}{ty_name}"
        return f"{full_func_path}.from_decoded({from_decoded_arg})"
    if isinstance(ty_type, IdlTypeArray):
        map_body = _field_from_decoded(
            idl=idl,
            ty=IdlField("item", docs=None, ty=ty_type.array[0]),
            val_prefix="",
            types_relative_imports=types_relative_imports,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{val_prefix}{ty_name}"
        return f"list(map(lambda item: {map_body}, {val_prefix}{ty_name}))"
    if ty_type in {
        IdlTypeSimple.Bool,
        *NUMBER_TYPES,
        IdlTypeSimple.String,
        IdlTypeSimple.PublicKey,
        IdlTypeSimple.Bytes,
    }:
        return f"{val_prefix}{ty_name}"
    raise ValueError(f"Unrecognized type: {ty_type}")


def _struct_field_initializer(
    idl: Idl,
    field: IdlField,
    types_relative_imports: bool,
    prefix: str = 'fields["',
    suffix: str = '"]',
) -> str:
    field_type = field.ty
    field_name = _sanitize(snake(field.name))
    if isinstance(field_type, IdlTypeDefined):
        defined = _sanitize(field_type.defined)
        filtered = [t for t in idl.types if _sanitize(t.name) == defined]
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        typedef_type = filtered[0].ty
        if isinstance(typedef_type, IdlTypeDefinitionTyStruct):
            module = snake(defined)
            defined_types_prefix = (
                "" if types_relative_imports else _DEFAULT_DEFINED_TYPES_PREFIX
            )
            obj_name = f"{defined_types_prefix}{module}.{defined}"
            return f"{obj_name}(**{prefix}{field_name}{suffix})"
        return f"{prefix}{field_name}{suffix}"
    if isinstance(field_type, IdlTypeOption):
        initializer = _struct_field_initializer(
            idl=idl,
            field=IdlField(field_name, docs=None, ty=field_type.option),
            prefix=prefix,
            suffix=suffix,
            types_relative_imports=types_relative_imports,
        )
        # skip coercion when not needed
        if initializer == f"{prefix}{field_name}{suffix}":
            return initializer
        return _maybe_none(f"{prefix}{field_name}{suffix}", initializer)
    if isinstance(field_type, IdlTypeArray):
        map_body = _struct_field_initializer(
            idl=idl,
            field=IdlField("item", docs=None, ty=field_type.array[0]),
            prefix="",
            suffix="",
            types_relative_imports=types_relative_imports,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{prefix}{field_name}{suffix}"
        return f"list(map(lambda item: {map_body}, {prefix}{field_name}{suffix}))"
    if isinstance(field_type, IdlTypeVec):
        map_body = _struct_field_initializer(
            idl=idl,
            field=IdlField("item", docs=None, ty=field_type.vec),
            prefix="",
            suffix="",
            types_relative_imports=types_relative_imports,
        )
        # skip mapping when not needed
        if map_body == "item":
            return f"{prefix}{field_name}{suffix}"
        return f"list(map(lambda item: {map_body}, {prefix}{field_name}{suffix}))"
    if field_type in {
        IdlTypeSimple.Bool,
        *NUMBER_TYPES,
        IdlTypeSimple.String,
        IdlTypeSimple.PublicKey,
        IdlTypeSimple.Bytes,
    }:
        return f"{prefix}{field_name}{suffix}"
    raise ValueError(f"Unrecognized type: {field_type}")


def _field_to_json(
    idl: Idl,
    ty: IdlField,
    val_prefix: str = "",
    val_suffix: str = "",
    convert_case: bool = True,
) -> str:
    ty_type = ty.ty
    maybe_converted = snake(ty.name) if convert_case else ty.name
    var_name = f"{val_prefix}{maybe_converted}{val_suffix}"
    if ty_type == IdlTypeSimple.PublicKey:
        return f"str({var_name})"
    if isinstance(ty_type, IdlTypeVec):
        map_body = _field_to_json(idl, IdlField("item", docs=None, ty=ty_type.vec))
        # skip mapping when not needed
        if map_body == "item":
            return var_name
        return f"list(map(lambda item: {map_body}, {var_name}))"
    if isinstance(ty_type, IdlTypeArray):
        map_body = _field_to_json(idl, IdlField("item", docs=None, ty=ty_type.array[0]))
        # skip mapping when not needed
        if map_body == "item":
            return var_name
        return f"list(map(lambda item: {map_body}, {var_name}))"
    if isinstance(ty_type, IdlTypeOption):
        value = _field_to_json(
            idl,
            IdlField(ty.name, docs=None, ty=ty_type.option),
            val_prefix,
            val_suffix,
            convert_case=convert_case,
        )
        # skip coercion when not needed
        if value == var_name:
            return value
        return _maybe_none(var_name, value)
    if isinstance(ty_type, IdlTypeDefined):
        defined = ty_type.defined
        filtered = [t for t in idl.types if t.name == defined]
        maybe_coption_split = defined.split("COption<")
        if len(maybe_coption_split) == 2:
            inner_type = maybe_coption_split[1][:-1]
            value = _field_to_json(
                idl,
                IdlField(
                    ty.name,
                    docs=None,
                    ty={"u64": IdlTypeSimple.U64, "Pubkey": IdlTypeSimple.PublicKey}[
                        inner_type
                    ],
                ),
                val_prefix,
                val_suffix,
                convert_case=convert_case,
            )
            # skip coercion when not needed
            if value == var_name:
                return value
            return _maybe_none(var_name, value)
        if len(filtered) != 1:
            raise ValueError(f"Type not found {defined}")
        return f"{var_name}.to_json()"
    if ty_type == IdlTypeSimple.Bytes:
        return f"list({var_name})"
    if ty_type in {
        IdlTypeSimple.Bool,
        *NUMBER_TYPES,
        IdlTypeSimple.String,
    }:
        return var_name
    raise ValueError(f"Unrecognized type: {ty_type}")


def _idl_type_to_json_type(ty: IdlType, types_relative_imports: bool) -> str:
    if isinstance(ty, IdlTypeVec):
        inner = _idl_type_to_json_type(
            ty=ty.vec, types_relative_imports=types_relative_imports
        )
        return f"list[{inner}]"
    if isinstance(ty, IdlTypeArray):
        inner = _idl_type_to_json_type(
            ty=ty.array[0], types_relative_imports=types_relative_imports
        )
        return f"list[{inner}]"
    if isinstance(ty, IdlTypeOption):
        inner = _idl_type_to_json_type(
            ty=ty.option, types_relative_imports=types_relative_imports
        )
        return f"typing.Optional[{inner}]"
    if isinstance(ty, IdlTypeDefined):
        defined = ty.defined
        maybe_coption_split = defined.split("COption<")
        if len(maybe_coption_split) == 2:
            inner_type = {"u64": "int", "Pubkey": "str"}[maybe_coption_split[1][:-1]]
            return f"typing.Optional[{inner_type}]"
        defined_types_prefix = (
            "" if types_relative_imports else _DEFAULT_DEFINED_TYPES_PREFIX
        )
        module = _sanitize(snake(defined))
        return f"{defined_types_prefix}{module}.{_json_interface_name(defined)}"
    if ty == IdlTypeSimple.Bool:
        return "bool"
    if ty in INT_TYPES:
        return "int"
    if ty in FLOAT_TYPES:
        return "float"
    if ty == IdlTypeSimple.Bytes:
        return "list[int]"
    if ty in {IdlTypeSimple.String, IdlTypeSimple.PublicKey}:
        return "str"
    raise ValueError(f"Unrecognized type: {ty}")


def _field_from_json(
    idl: Idl,
    ty: IdlField,
    types_relative_imports: bool,
    param_prefix: str = 'obj["',
    param_suffix: str = '"]',
) -> str:
    ty_type = ty.ty
    ty_name_snake_unsanitized = snake(ty.name)
    ty_name = _sanitize(ty_name_snake_unsanitized)
    var_name = f"{param_prefix}{ty_name_snake_unsanitized}{param_suffix}"
    if ty_type == IdlTypeSimple.PublicKey:
        return f"Pubkey.from_string({var_name})"
    if isinstance(ty_type, IdlTypeVec):
        map_body = _field_from_json(
            idl=idl,
            ty=IdlField("item", docs=None, ty=ty_type.vec),
            param_prefix="",
            param_suffix="",
            types_relative_imports=types_relative_imports,
        )
        # skip mapping when not needed
        if map_body == "item":
            return var_name
        return f"list(map(lambda item: {map_body}, {var_name}))"
    if isinstance(ty_type, IdlTypeArray):
        map_body = _field_from_json(
            idl=idl,
            ty=IdlField("item", docs=None, ty=ty_type.array[0]),
            param_prefix="",
            param_suffix="",
            types_relative_imports=types_relative_imports,
        )
        # skip mapping when not needed
        if map_body == "item":
            return var_name
        return f"list(map(lambda item: {map_body}, {var_name}))"
    if isinstance(ty_type, IdlTypeOption):
        inner = _field_from_json(
            idl=idl,
            ty=IdlField(ty_name, docs=None, ty=ty_type.option),
            param_prefix=param_prefix,
            param_suffix=param_suffix,
            types_relative_imports=types_relative_imports,
        )
        # skip coercion when not needed
        if inner == var_name:
            return inner
        return _maybe_none(var_name, inner)
    if isinstance(ty_type, IdlTypeDefined):
        from_json_arg = var_name
        defined = _sanitize(ty_type.defined)
        maybe_coption_split = defined.split("COption<")
        if len(maybe_coption_split) == 2:
            inner_type = maybe_coption_split[1][:-1]
            inner = _field_from_json(
                idl=idl,
                ty=IdlField(
                    ty_name,
                    docs=None,
                    ty={"u64": IdlTypeSimple.U64, "Pubkey": IdlTypeSimple.PublicKey}[
                        inner_type
                    ],
                ),
                param_prefix=param_prefix,
                param_suffix=param_suffix,
                types_relative_imports=types_relative_imports,
            )
            # skip coercion when not needed
            if inner == var_name:
                return inner
            return _maybe_none(var_name, inner)
        defined_snake = _sanitize(snake(ty_type.defined))
        filtered = [t for t in idl.types if _sanitize(t.name) == defined]
        typedef_type = filtered[0].ty
        from_json_func_path = (
            f"{defined_snake}.{defined}"
            if isinstance(typedef_type, IdlTypeDefinitionTyStruct)
            else f"{defined_snake}"
        )
        defined_types_prefix = (
            "" if types_relative_imports else _DEFAULT_DEFINED_TYPES_PREFIX
        )
        full_func_path = f"{defined_types_prefix}{from_json_func_path}"
        return f"{full_func_path}.from_json({from_json_arg})"
    if ty_type == IdlTypeSimple.Bytes:
        return f"bytes({var_name})"
    if ty_type in {
        IdlTypeSimple.Bool,
        *NUMBER_TYPES,
        IdlTypeSimple.String,
    }:
        return var_name
    raise ValueError(f"Unrecognized type: {ty_type}")
