from typing import List, Dict, Any

import inflection
from construct import Construct
from borsh import (
    CStruct,
    TupleStruct,
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
)
from anchorpy.borsh_extension import PublicKey
from anchorpy.idl import IdlField, IdlTypeDef


FIELD_TYPE_MAP: Dict[str, Any] = {
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
    "publicKey": PublicKey,
}


def typedef_layout(
    typedef: IdlTypeDef, types: List[IdlTypeDef], name: str = ""
) -> Construct:
    if typedef.type.kind == "struct":
        field_layouts = [field_layout(field, types) for field in typedef.type.fields]
        return CStruct(field_layouts, name)
    elif typedef.type.kind == "enum":
        variants = []
        for variant in typedef.type.variants:
            name = inflection.camelize(variant.name)
            if not variant.fields:
                variants.append(CStruct([], name))
            else:
                fields = []
                for f in variant.fields:
                    if not f.name:
                        raise Exception("Tuple enum variants not yet implemented")
                    fields.append(field_layout(f, types))
                variants.append(CStruct(fields, name))
        return Enum(variants, name)
    else:
        raise Exception(f"Unknown type {typedef.type.kind}")


def field_layout(field: IdlField, types: List[IdlTypeDef]) -> Construct:
    # This method might diverge a bit from anchor.ts stuff but the behavior should be the sames
    field_name = inflection.camelize(field.name, False) if field.name else ""
    if not isinstance(field.type, dict) and field.type in FIELD_TYPE_MAP:
        return field_name / FIELD_TYPE_MAP[field.type]
    else:
        type_ = list(field.type.keys())[0]
        if type_ == "vec":
            return Vector(
                field_layout(IdlField(name="", type=field.type["vec"]), types),
                field_name,
            )
        elif type_ == "option":
            raise Exception("TODO: option type")
        elif type_ == "defined":
            if not types:
                raise Exception("User defined types not provided")
            filtered = list(filter(lambda t: t.name == field.type["defined"], types))
            if len(filtered) != 1:
                raise Exception(f"Type not found {field.type['defined']}")
            return typedef_layout(filtered[0], types, field_name)
        elif type_ == "array":
            array_ty = field.type["array"][0]
            array_len = field.type["array"][1]
            inner_layout = field_layout(IdlField(name="", type=array_ty), types)
            return Array(inner_layout, array_len, field_name)
        else:
            raise Exception(f"Field {field} not implemented yet")
