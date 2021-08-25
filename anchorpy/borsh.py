import enum
import struct
from typing import Callable, Tuple, Optional, Union, Protocol, NamedTuple, cast
from dataclasses import dataclass
import io
import traceback
from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import Dict, List, Any, Tuple
from construct_typed import DataclassMixin
from construct import (
    Int8ul,
    Flag,
    Int8sl,
    Int16sl,
    Int16ul,
    Int32sl,
    Int32ul,
    Int64ul,
    Int64sl,
    BytesInteger,
    Container,
    Adapter,
    Default,
    GreedyBytes,
    Prefixed,
    GreedyString,
    Enum,
)
import construct

from sumtypes import sumtype, constructor
from solana import publickey
import attr

TUPLE_DATA = "tuple_data"


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


@rust_enum
class MyType:
    # constructors specify names for their arguments
    MyConstructor = tuple_struct()
    AnotherConstructor = clike_struct("x", "y")
    Argless = unit_struct()
    Argless2 = unit_struct()


@rust_enum
class Message:
    Quit = unit_struct()
    Move = clike_struct("x", "y")
    Write = tuple_struct()
    ChangeColor = tuple_struct()


class Layout(ABC):
    def __init__(self, field_name: str):
        self.field_name = field_name

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.field_name}>"

    @abstractmethod
    def encode(self, data: Any) -> bytes:
        ...

    @abstractmethod
    def decode(self, b: bytes) -> Any:
        """
        Modifies b in place
        """
        ...


class Dataclass(Protocol):
    # as already noted in comments, checking for this attribute is currently
    # the most reliable way to ascertain that something is a dataclass
    __dataclass_fields__: Dict


class BorshSimpleType2(Layout, ABC):
    def __init__(self, field_name: str, fmt: Any):
        super().__init__(field_name)
        self.fmt = fmt

    def encode(self, data: Any) -> bytes:
        return self.fmt.build(data)

    def decode(self, b: bytes) -> Any:
        return self.fmt.parse(b)


class Bool(BorshSimpleType2):
    def __init__(self, field_name: str):
        super().__init__(field_name, Flag)


class U8(BorshSimpleType2):
    def __init__(self, field_name: str):
        super().__init__(field_name, Int8ul)


class I8(BorshSimpleType2):
    def __init__(self, field_name: str):
        super().__init__(field_name, Int8sl)


class U16(BorshSimpleType2):
    def __init__(self, field_name: str):
        super().__init__(field_name, Int16ul)


class I16(BorshSimpleType2):
    def __init__(self, field_name: str):
        super().__init__(field_name, Int16sl)


class U32(BorshSimpleType2):
    def __init__(self, field_name: str):
        super().__init__(field_name, Int32ul)


class I32(BorshSimpleType2):
    def __init__(self, field_name: str):
        super().__init__(field_name, Int32sl)


class U64(BorshSimpleType2):
    def __init__(self, field_name: str):
        super().__init__(field_name, Int64ul)


class I64(BorshSimpleType2):
    def __init__(self, field_name: str):
        super().__init__(field_name, Int64sl)


class U128(BorshSimpleType2):
    def __init__(self, field_name: str):
        n_bytes = 16
        super().__init__(field_name, BytesInteger(n_bytes, signed=False, swapped=True))


class I128(BorshSimpleType2):
    def __init__(self, field_name: str):
        n_bytes = 16
        super().__init__(field_name, BytesInteger(n_bytes, signed=True, swapped=True))


BorshBytes = Prefixed(Int32ul, GreedyBytes)


class StringAdapter(Adapter):
    def _decode(self, obj: bytes, context, path) -> str:
        return obj.decode("utf8")

    def _encode(self, obj: str, context, path) -> bytes:
        return bytes(obj, "utf8")


BorshString = StringAdapter(BorshBytes)


class String(BorshSimpleType2):
    def __init__(self, field_name: str):
        super().__init__(field_name, BorshString)


class PublicKeyAdapter(Adapter):
    def _decode(self, obj: str, context, path) -> publickey.PublicKey:
        return publickey.PublicKey(obj)

    def _encode(self, obj: publickey.PublicKey, context, path) -> str:
        return str(obj)


PublicKey = PublicKeyAdapter(BorshString)


class BorshOption(construct.Subconstruct):
    def __init__(self, subcon):
        super().__init__(subcon)
        self.is_none_flag = b"\x00"
        self.is_some_flag = b"\x01"

    def _parse(self, stream, context, path):
        discriminator = construct.stream_read(stream, 1, path)
        if discriminator == self.is_none_flag:
            return None
        return self.subcon._parse(stream, context, path)

    def _build(self, obj, stream, context, path):
        if obj is None:
            return construct.stream_write(stream, self.is_none_flag, 1, path)
        construct.stream_write(stream, self.is_some_flag, 1, path)
        buildret = self.subcon._build(obj, stream, context, path)
        return buildret

    def _sizeof(self, context, path):
        raise construct.SizeofError(path=path)


class BorshEnum(construct.Construct):
    def __init__(self, *variants) -> None:
        super().__init__()
        self.variants = variants

        class EnumDef:
            pass

        for variant in variants:
            if isinstance(variant, str):
                setattr(EnumDef, variant, unit_struct())
            else:
                variant_name = variant.name
                if variant_name is None:
                    raise ValueError("Unnamed enum variants not allowed.")
                underlying_variant = (
                    variant.subcon
                    if isinstance(variant, construct.Renamed)
                    else variant
                )
                if isinstance(underlying_variant, construct.Sequence):
                    setattr(EnumDef, variant_name, tuple_struct())
                elif isinstance(underlying_variant, construct.Struct):
                    subcon_names: List[str] = []
                    for s in underlying_variant.subcons:
                        name = s.name
                        if not isinstance(name, str):
                            raise ValueError("Variant names must be strings.")
                        if name is None:
                            raise ValueError("Unnamed struct fields not allowed.")
                        if name == TUPLE_DATA:
                            raise ValueError(
                                f"The name {TUPLE_DATA} is reserved. If you encountered this "
                                "error it's either a wild coincidence or you're doing it wrong."
                            )
                        if name[0] == "_":
                            raise ValueError(
                                "Variant names cannot start with an underscore."
                            )
                        subcon_names.append(cast(str, name))
                    setattr(EnumDef, variant_name, clike_struct(*subcon_names))
                else:
                    raise ValueError(
                        f"Unrecognized variant type: {type(underlying_variant)}"
                    )

        self.enum = rust_enum(EnumDef)

    def _parse(self, stream, context, path):
        index_bytes = construct.stream_read(stream, 1, path)
        index = Int8ul.parse(index_bytes)
        variant = self.enum.getitem(index)
        parser = self.variants[index]
        if isinstance(parser, str):
            return variant()
        container = parser._parse(stream, context, path)
        if isinstance(container, construct.Container):
            as_dict = {key: val for key, val in container.items() if key[0] != "_"}
            return variant(**as_dict)
        return variant(tuple(container))

    def _build(self, obj, stream, context, path):
        index = obj.index
        index_as_bytes = Int8ul.build(index)
        builder = self.variants[index]
        as_dict = attr.asdict(obj)
        buildret = construct.stream_write(stream, index_as_bytes, 1, path)
        if as_dict:
            try:
                to_build = as_dict[TUPLE_DATA]
            except KeyError:
                to_build = as_dict
            return builder._build(to_build, stream, context, path)
        return buildret

    def _sizeof(self, context, path):
        raise construct.SizeofError(path=path)


class Vector(Layout):
    def __init__(self, layout: Layout, name: str = ""):
        super().__init__(name)
        self.layout = layout

    def encode(self, data: Any) -> bytes:
        vec_len_byte = struct.pack("<I", len(data))
        b = bytes()
        for d in data:
            b += self.layout.encode(d)
        return vec_len_byte + b

    def decode(self, b: bytes) -> Tuple[bytes, Any]:
        vec = list()
        vec_len = struct.unpack("<I", b[:4])[0]
        bytes_left = b[4:]
        for idx in range(vec_len):
            bytes_left, decoded = self.layout.decode(bytes_left)
            vec.append(decoded)
        return bytes_left, vec


class Array(Layout):
    def __init__(self, layout: Layout, length: int, name: str = ""):
        super().__init__(name)
        self.layout = layout
        self.length = length

    def __repr__(self):
        return (
            f"Array<layout={self.layout}, length={self.length}, name={self.field_name}>"
        )

    def encode(self, data: List[Any]) -> bytes:
        if len(data) != self.length:
            raise Exception(
                f"Array {self.field_name} expected length {self.length}, got {len(data)}"
            )
        b = bytes()
        for d in data:
            b += self.layout.encode(d)
        return b

    def decode(self, b: bytes) -> Tuple[bytes, List[Any]]:
        decoded = list()
        bytes_left = b
        for i in range(self.length):
            bytes_left, d = self.layout.decode(bytes_left)
            decoded.append(d)
        return bytes_left, decoded


class CStruct(Adapter):
    def __init__(self, defn) -> None:
        super().__init__()
        self.defn = defn

    def _decode(self, obj: bytes, context, path) -> str:
        return self.defn(**obj)

    def _encode(self, obj: str, context, path) -> bytes:
        return obj


class Struct(Layout):
    def __init__(self, field_layouts: List[Layout], name: str = ""):
        super().__init__(name)
        self.field_layouts = field_layouts

    def __repr__(self):
        return f"Struct<name={self.field_name}, field_layouts={self.field_layouts}>"

    def encode(self, data: Any) -> bytes:
        if len(data) != len(self.field_layouts):
            raise Exception(f"{len(data)} != {len(self.field_layouts)}")
        b = bytes()
        for layout in self.field_layouts:
            encoded = layout.encode(data[layout.field_name])
            b += encoded
        return b

    def decode(self, b: bytes) -> Tuple[bytes, Any]:
        ret = SimpleNamespace()
        bytes_left = b
        for layout in self.field_layouts:
            # decode modifies b in place so the offsets are computed automatically for the next layout
            try:
                # print(f"decoding: {layout.field_name}, {layout.__class__.__name__}bytes={bytes_left}", flush=True)
                bytes_left, decoded = layout.decode(bytes_left)
                setattr(ret, layout.field_name, decoded)
            except:
                print(traceback.format_exc(), flush=True)
                raise
        return bytes_left, ret


class Struct2(BorshSimpleType2):
    def __init__(self, field_layouts: construct.Struct, name: str = ""):
        super().__init__(field_name=name, fmt=field_layouts)

    def __repr__(self):
        return f"Struct<name={self.field_name}, field_layouts={self.fmt}>"

    def encode(self, data: Dict[str, Any]) -> bytes:
        return self.fmt.build(data)

    def decode(self, b: bytes) -> Container:
        return self.fmt.parse(b)


class Option(BorshSimpleType2):
    def __init__(self, field_name: str, fmt: Any):
        super().__init__(field_name=field_name, fmt=BorshOption(fmt))


def main():
    TEST_CASES = [
        (Bool, True),
        (Bool, False),
        (U8, 10),
        (I8, -126),
        (U16, 0xDEAD),
        (I16, 0xEAD),
        (U32, 0xDEADBEEF),
        (I32, 0xEADBEEF),
        (U64, 0xDEADBEEFDEADBEEF),
        (I64, 0xEADBEEFDEADBEEF),
        (U128, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
        (I128, 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
        (I128, -1),
        (String, "testing 1234"),
    ]

    for datatype, input_val in TEST_CASES:
        t = datatype("foo")
        # print(f"Datatype={datatype}, input={input_val}")

        encoded = t.encode(input_val)
        decoded = t.decode(encoded)
        try:
            assert input_val == decoded
        except AssertionError:
            print(f"input val: {input_val}")
            print(f"decoded: {decoded}")

    s = Struct2(
        construct.Struct(
            "myu128" / BytesInteger(16, signed=False, swapped=True),
            "string_field" / BorshString,
            "myu128_1" / BytesInteger(16, signed=False, swapped=True),
        ),
        "struct_name",
    )
    struct_encoded = s.encode(
        {
            "myu128": 123456,
            "string_field": "abc",
            "myu128_1": 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        }
    )
    print(f"struct_encoded: {list(struct_encoded)}")
    ret = s.decode(struct_encoded)
    assert ret.string_field == "abc"
    assert ret.myu128 == 123456
    assert ret.myu128_1 == 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

    pk = publickey.PublicKey("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i99")
    assert PublicKey.parse(PublicKey.build(pk)) == pk

    v = Vector(U128("foo"), "vector")
    encoded = v.encode([1, 2, 3, 4])
    # print(encoded)
    # print(len(encoded))
    bytes_left, decoded = v.decode(v.encode([1, 2, 3, 4]))
    assert decoded == [1, 2, 3, 4]

    v2 = Vector(String("s"), "vector")
    bytes_left, decoded = v2.decode(v2.encode(["a", "b", "c", "d", "e"]))
    print(decoded)

    a = Array(String(""), 5, "some_arr")
    bytes_left, decoded = a.decode(a.encode(["a", "b", "c", "d", "e", "f"]))
    print(decoded)


if __name__ == "__main__":
    main()
