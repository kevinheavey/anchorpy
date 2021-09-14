from typing import Optional, cast, List, Tuple, Any, TYPE_CHECKING
from construct import (
    Flag as Bool,
    Int8ul as U8,
    Int8sl as I8,
    Int16ul as U16,
    Int16sl as I16,
    Int32ul as U32,
    Int32sl as I32,
    Int64ul as U64,
    Int64sl as I64,
    BytesInteger,
    Adapter,
    GreedyBytes,
    Prefixed,
    PrefixedArray,
    Sequence as TupleStruct,
    Struct as CStruct,
    Construct,
    Renamed,
    Array,
    FormatField,
    FormatFieldError,
    singleton,
    Switch,
    IfThenElse,
    Pass,
)

if TYPE_CHECKING:
    from construct import (
        SubconBuildTypes,
        BuildTypes,
        Context,
        PathType,
    )
from sumtypes import sumtype, constructor
from solana import publickey
import attr
from math import isnan

TUPLE_DATA = "tuple_data"


class FormatFieldNoNan(FormatField):
    """Adapted form of `construct.FormatField` that forbids nan."""

    def _parse(self, stream, context, path):
        result = super()._parse(stream, context, path)
        if isnan(result):
            raise FormatFieldError("Borsh does not support nan.")
        return result

    def _build(self, obj, stream, context, path):
        if isnan(obj):
            raise ValueError("Borsh does not support nan.")
        return super()._build(obj, stream, context, path)


@singleton
def F32() -> FormatFieldNoNan:  # noqa: N802
    """Little endian, 32-bit IEEE floating point number."""
    return FormatFieldNoNan("<", "f")


@singleton
def F64() -> FormatFieldNoNan:  # noqa: N802
    """Little endian, 64-bit IEEE floating point number."""
    return FormatFieldNoNan("<", "d")


def rust_enum(klass):
    indexed = sumtype(klass)
    for idx, cname in enumerate(indexed._sumtype_constructor_names):  # noqa: WPS437
        constructr = getattr(indexed, cname)
        constructr.index = idx

    @classmethod
    def getitem(cls, _index: int):  # __getitem__ magic method cannot be classmethod
        return getattr(cls, cls._sumtype_constructor_names[_index])

    indexed.getitem = getitem

    return indexed


def tuple_struct():
    return constructor(**{TUPLE_DATA: attr.ib(type=tuple)})


def unit_struct():
    return constructor()


def clike_struct(*fields: str):
    return constructor(*fields)


def Vec(subcon: Construct) -> Array:  # noqa: N802
    return PrefixedArray(U32, subcon)


Bytes = Prefixed(U32, GreedyBytes)


class _String(Adapter):
    def __init__(self) -> None:
        super().__init__(Bytes)

    def _decode(self, obj: bytes, context, path) -> str:
        return obj.decode("utf8")

    def _encode(self, obj: str, context, path) -> bytes:
        return bytes(obj, "utf8")


String = _String()


U128 = BytesInteger(16, signed=False, swapped=True)
I128 = BytesInteger(16, signed=True, swapped=True)


class PublicKey(Adapter):
    def __init__(self) -> None:
        super().__init__(String)

    def _decode(self, obj: str, context, path) -> publickey.PublicKey:
        return publickey.PublicKey(obj)

    def _encode(self, obj: publickey.PublicKey, context, path) -> str:
        return str(obj)


# class Option(Subconstruct):
#     def __init__(self, subcon):
#         super().__init__(subcon)
#         self.is_none_flag = b"\x00"
#         self.is_some_flag = b"\x01"

#     def _parse(self, stream, context, path):
#         discriminator = stream_read(stream, 1, path)
#         if discriminator == self.is_none_flag:
#             return None
#         return self.subcon._parse(stream, context, path)  # noqa: WPS437

#     def _build(self, obj, stream, context, path):
#         if obj is None:
#             return stream_write(stream, self.is_none_flag, 1, path)
#         stream_write(stream, self.is_some_flag, 1, path)
#         return self.subcon._build(obj, stream, context, path)  # noqa: WPS437

#     def _sizeof(self, context, path):
#         raise SizeofError(path=path)


class Option(Adapter):
    _discriminator_key = "discriminator"
    _value_key = "value"

    def __init__(self, subcon: Construct) -> None:
        option_struct = CStruct(
            self._discriminator_key / U8,
            self._value_key
            / IfThenElse(lambda this: this[self._discriminator_key] == 0, Pass, subcon),
        )
        super().__init__(option_struct)

    def _decode(self, obj: Any, context, path) -> Any:
        return obj[self._value_key]

    def _encode(self, obj: Any, context, path) -> str:
        discriminator = 0 if obj is None else 1
        return {self._discriminator_key: discriminator, self._value_key: obj}


def _check_name_not_null(name: Optional[str]) -> None:
    if name is None:
        raise ValueError("Unnamed struct fields not allowed.")


def _check_variant_name(name: Optional[str]) -> None:
    _check_name_not_null(name)
    if not isinstance(name, str):
        raise ValueError("Variant names must be strings.")
    if name == TUPLE_DATA:
        raise ValueError(
            f"The name {TUPLE_DATA} is reserved. If you encountered this "
            "error it's either a wild coincidence or you're doing it wrong."
        )
    if name[0] == "_":
        raise ValueError("Variant names cannot start with an underscore.")


def _handle_cstruct_variant(underlying_variant, variant_name, enum_def) -> None:
    subcon_names: List[str] = []
    for s in underlying_variant.subcons:
        name = s.name
        _check_variant_name(name)
        subcon_names.append(cast(str, name))
    setattr(enum_def, variant_name, clike_struct(*subcon_names))


def _handle_struct_variant(variant, enum_def) -> None:
    variant_name = variant.name
    if variant_name is None:
        raise ValueError("Unnamed enum variants not allowed.")
    underlying_variant = variant.subcon if isinstance(variant, Renamed) else variant
    if isinstance(underlying_variant, TupleStruct):
        setattr(enum_def, variant_name, tuple_struct())
    elif isinstance(underlying_variant, CStruct):
        _handle_cstruct_variant(underlying_variant, variant_name, enum_def)
    else:
        variant_type = type(underlying_variant)
        raise ValueError(f"Unrecognized variant type: {variant_type}")


def _make_enum(*variants):
    class EnumDef:  # noqa: WPS431
        """Python representation of Rust's Enum type."""

    for variant in variants:
        if isinstance(variant, str):
            setattr(EnumDef, variant, unit_struct())
        else:
            _handle_struct_variant(variant, EnumDef)

    return rust_enum(EnumDef)


class Enum(Adapter):
    _index_key = "index"
    _value_key = "value"

    def __init__(self, *variants) -> None:
        self.enum = _make_enum(*variants)
        self.variants = variants
        switch_cases = {}
        for idx, var in enumerate(variants):
            if isinstance(var, str):
                parser = Pass
            else:
                parser = var
            switch_cases[idx] = parser
        enum_struct = CStruct(
            self._index_key / U8,
            self._value_key / Switch(lambda this: this.index, switch_cases),
        )
        super().__init__(enum_struct)

    def _decode(self, obj: Any, context, path) -> Any:
        enum_variant = self.enum.getitem(obj.index)
        if obj.value is None:
            return enum_variant()
        return enum_variant(obj.value)

    def _encode(self, obj: Any, context, path) -> str:
        index = obj.index
        as_dict = attr.asdict(obj)
        if as_dict:
            try:
                to_build = as_dict[TUPLE_DATA]
            except KeyError:
                to_build = as_dict
        else:
            to_build = None
        return {self._index_key: index, self._value_key: to_build}


class HashMap(Adapter):
    def __init__(self, key_subcon, value_subcon) -> None:
        super().__init__(PrefixedArray(U32, TupleStruct(key_subcon, value_subcon)))

    def _decode(self, obj: List[Tuple], context, path) -> dict:
        return dict(obj)

    def _encode(self, obj, context, path) -> List[Tuple]:
        return sorted(obj.items())


class HashSet(Adapter):
    def __init__(self, subcon) -> None:
        super().__init__(PrefixedArray(U32, subcon))

    def _decode(
        self, obj: "SubconBuildTypes", context: "Context", path: "PathType"
    ) -> set:
        return set(obj)

    def _encode(self, obj: "BuildTypes", context: "Context", path: "PathType") -> list:
        return sorted(obj)


def main():
    enum = Enum(
        "Unit",
        "TupleVariant" / TupleStruct(U128, String, I64, Option(U16)),
        "CStructVariant"
        / CStruct("u128_field" / U128, "string_field" / String, "vec_field" / Vec(U16)),
    )
    type_input_expected = [
        (U8, 255, [255]),
        (I8, -128, [128]),
        (U16, 65535, [255, 255]),
        (I16, -32768, [0, 128]),
        (U32, 4294967295, [255, 255, 255, 255]),
        (I32, -2147483648, [0, 0, 0, 128]),
        (U64, 18446744073709551615, [255, 255, 255, 255, 255, 255, 255, 255]),
        (I64, -9223372036854775808, [0, 0, 0, 0, 0, 0, 0, 128]),
        (
            U128,
            340282366920938463463374607431768211455,
            [
                255,
                255,
                255,
                255,
                255,
                255,
                255,
                255,
                255,
                255,
                255,
                255,
                255,
                255,
                255,
                255,
            ],
        ),
        (
            I128,
            -170141183460469231731687303715884105728,
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 128],
        ),
        (F32, 0.2, [205, 204, 76, 62]),
        (F64, -0.2, [154, 153, 153, 153, 153, 153, 201, 191]),
        (I16[3], [1, 2, 3], [1, 0, 2, 0, 3, 0]),
        (Vec(I16), [1, 1], [2, 0, 0, 0, 1, 0, 1, 0]),
        (
            TupleStruct(U128, String, I64, Option(U16)),
            [123, "hello", 1400, 13],
            [
                123,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                5,
                0,
                0,
                0,
                104,
                101,
                108,
                108,
                111,
                120,
                5,
                0,
                0,
                0,
                0,
                0,
                0,
                1,
                13,
                0,
            ],
        ),
        (
            CStruct(
                "u128_field" / U128, "string_field" / String, "vec_field" / Vec(U16)
            ),
            {"u128_field": 1033, "string_field": "hello", "vec_field": [1, 2, 3]},
            [
                9,
                4,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                5,
                0,
                0,
                0,
                104,
                101,
                108,
                108,
                111,
                3,
                0,
                0,
                0,
                1,
                0,
                2,
                0,
                3,
                0,
            ],
        ),
        (enum, enum.enum.Unit(), [0]),
        (
            enum,
            enum.enum.TupleVariant([10, "hello", 13, 12]),
            [
                1,
                10,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                5,
                0,
                0,
                0,
                104,
                101,
                108,
                108,
                111,
                13,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                1,
                12,
                0,
            ],
        ),
        (
            enum,
            enum.enum.CStructVariant(
                u128_field=15,
                string_field="hi",
                vec_field=[3, 2, 1],
            ),
            [
                2,
                15,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                2,
                0,
                0,
                0,
                104,
                105,
                3,
                0,
                0,
                0,
                3,
                0,
                2,
                0,
                1,
                0,
            ],
        ),
        (
            HashMap(U8, enum),
            {2: enum.enum.Unit(), 1: enum.enum.TupleVariant([11, "hello", 123, None])},
            [
                2,
                0,
                0,
                0,
                1,
                1,
                11,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                5,
                0,
                0,
                0,
                104,
                101,
                108,
                108,
                111,
                123,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                2,
                0,
            ],
        ),
        (HashSet(U8), {1, 2, 3}, [3, 0, 0, 0, 1, 2, 3]),
        (String, "🚀", [4, 0, 0, 0, 240, 159, 154, 128]),
    ]
    for type_, input_, expected in type_input_expected:
        result = list(type_.build(input_))
        assert result == expected

    # pk = publickey.PublicKey("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i99")
    # assert PublicKey.parse(PublicKey.build(pk)) == pk


if __name__ == "__main__":
    main()
