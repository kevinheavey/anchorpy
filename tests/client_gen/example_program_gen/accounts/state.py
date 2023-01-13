import typing
from dataclasses import dataclass
from construct import Construct
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
import borsh_construct as borsh
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from anchorpy.utils.rpc import get_multiple_accounts
from anchorpy.borsh_extension import BorshPubkey
from ..program_id import PROGRAM_ID
from .. import types


class StateJSON(typing.TypedDict):
    bool_field: bool
    u8_field: int
    i8_field: int
    u16_field: int
    i16_field: int
    u32_field: int
    i32_field: int
    f32_field: float
    u64_field: int
    i64_field: int
    f64_field: float
    u128_field: int
    i128_field: int
    bytes_field: list[int]
    string_field: str
    pubkey_field: str
    vec_field: list[int]
    vec_struct_field: list[types.foo_struct.FooStructJSON]
    option_field: typing.Optional[bool]
    option_struct_field: typing.Optional[types.foo_struct.FooStructJSON]
    struct_field: types.foo_struct.FooStructJSON
    array_field: list[bool]
    enum_field1: types.foo_enum.FooEnumJSON
    enum_field2: types.foo_enum.FooEnumJSON
    enum_field3: types.foo_enum.FooEnumJSON
    enum_field4: types.foo_enum.FooEnumJSON


@dataclass
class State:
    discriminator: typing.ClassVar = b"\xd8\x92k^hK\xb6\xb1"
    layout: typing.ClassVar = borsh.CStruct(
        "bool_field" / borsh.Bool,
        "u8_field" / borsh.U8,
        "i8_field" / borsh.I8,
        "u16_field" / borsh.U16,
        "i16_field" / borsh.I16,
        "u32_field" / borsh.U32,
        "i32_field" / borsh.I32,
        "f32_field" / borsh.F32,
        "u64_field" / borsh.U64,
        "i64_field" / borsh.I64,
        "f64_field" / borsh.F64,
        "u128_field" / borsh.U128,
        "i128_field" / borsh.I128,
        "bytes_field" / borsh.Bytes,
        "string_field" / borsh.String,
        "pubkey_field" / BorshPubkey,
        "vec_field" / borsh.Vec(typing.cast(Construct, borsh.U64)),
        "vec_struct_field"
        / borsh.Vec(typing.cast(Construct, types.foo_struct.FooStruct.layout)),
        "option_field" / borsh.Option(borsh.Bool),
        "option_struct_field" / borsh.Option(types.foo_struct.FooStruct.layout),
        "struct_field" / types.foo_struct.FooStruct.layout,
        "array_field" / borsh.Bool[3],
        "enum_field1" / types.foo_enum.layout,
        "enum_field2" / types.foo_enum.layout,
        "enum_field3" / types.foo_enum.layout,
        "enum_field4" / types.foo_enum.layout,
    )
    bool_field: bool
    u8_field: int
    i8_field: int
    u16_field: int
    i16_field: int
    u32_field: int
    i32_field: int
    f32_field: float
    u64_field: int
    i64_field: int
    f64_field: float
    u128_field: int
    i128_field: int
    bytes_field: bytes
    string_field: str
    pubkey_field: Pubkey
    vec_field: list[int]
    vec_struct_field: list[types.foo_struct.FooStruct]
    option_field: typing.Optional[bool]
    option_struct_field: typing.Optional[types.foo_struct.FooStruct]
    struct_field: types.foo_struct.FooStruct
    array_field: list[bool]
    enum_field1: types.foo_enum.FooEnumKind
    enum_field2: types.foo_enum.FooEnumKind
    enum_field3: types.foo_enum.FooEnumKind
    enum_field4: types.foo_enum.FooEnumKind

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["State"]:
        resp = await conn.get_account_info(address, commitment=commitment)
        info = resp.value
        if info is None:
            return None
        if info.owner != program_id:
            raise ValueError("Account does not belong to this program")
        bytes_data = info.data
        return cls.decode(bytes_data)

    @classmethod
    async def fetch_multiple(
        cls,
        conn: AsyncClient,
        addresses: list[Pubkey],
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.List[typing.Optional["State"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["State"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "State":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = State.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            bool_field=dec.bool_field,
            u8_field=dec.u8_field,
            i8_field=dec.i8_field,
            u16_field=dec.u16_field,
            i16_field=dec.i16_field,
            u32_field=dec.u32_field,
            i32_field=dec.i32_field,
            f32_field=dec.f32_field,
            u64_field=dec.u64_field,
            i64_field=dec.i64_field,
            f64_field=dec.f64_field,
            u128_field=dec.u128_field,
            i128_field=dec.i128_field,
            bytes_field=dec.bytes_field,
            string_field=dec.string_field,
            pubkey_field=dec.pubkey_field,
            vec_field=dec.vec_field,
            vec_struct_field=list(
                map(
                    lambda item: types.foo_struct.FooStruct.from_decoded(item),
                    dec.vec_struct_field,
                )
            ),
            option_field=dec.option_field,
            option_struct_field=(
                None
                if dec.option_struct_field is None
                else types.foo_struct.FooStruct.from_decoded(dec.option_struct_field)
            ),
            struct_field=types.foo_struct.FooStruct.from_decoded(dec.struct_field),
            array_field=dec.array_field,
            enum_field1=types.foo_enum.from_decoded(dec.enum_field1),
            enum_field2=types.foo_enum.from_decoded(dec.enum_field2),
            enum_field3=types.foo_enum.from_decoded(dec.enum_field3),
            enum_field4=types.foo_enum.from_decoded(dec.enum_field4),
        )

    def to_json(self) -> StateJSON:
        return {
            "bool_field": self.bool_field,
            "u8_field": self.u8_field,
            "i8_field": self.i8_field,
            "u16_field": self.u16_field,
            "i16_field": self.i16_field,
            "u32_field": self.u32_field,
            "i32_field": self.i32_field,
            "f32_field": self.f32_field,
            "u64_field": self.u64_field,
            "i64_field": self.i64_field,
            "f64_field": self.f64_field,
            "u128_field": self.u128_field,
            "i128_field": self.i128_field,
            "bytes_field": list(self.bytes_field),
            "string_field": self.string_field,
            "pubkey_field": str(self.pubkey_field),
            "vec_field": self.vec_field,
            "vec_struct_field": list(
                map(lambda item: item.to_json(), self.vec_struct_field)
            ),
            "option_field": self.option_field,
            "option_struct_field": (
                None
                if self.option_struct_field is None
                else self.option_struct_field.to_json()
            ),
            "struct_field": self.struct_field.to_json(),
            "array_field": self.array_field,
            "enum_field1": self.enum_field1.to_json(),
            "enum_field2": self.enum_field2.to_json(),
            "enum_field3": self.enum_field3.to_json(),
            "enum_field4": self.enum_field4.to_json(),
        }

    @classmethod
    def from_json(cls, obj: StateJSON) -> "State":
        return cls(
            bool_field=obj["bool_field"],
            u8_field=obj["u8_field"],
            i8_field=obj["i8_field"],
            u16_field=obj["u16_field"],
            i16_field=obj["i16_field"],
            u32_field=obj["u32_field"],
            i32_field=obj["i32_field"],
            f32_field=obj["f32_field"],
            u64_field=obj["u64_field"],
            i64_field=obj["i64_field"],
            f64_field=obj["f64_field"],
            u128_field=obj["u128_field"],
            i128_field=obj["i128_field"],
            bytes_field=bytes(obj["bytes_field"]),
            string_field=obj["string_field"],
            pubkey_field=Pubkey.from_string(obj["pubkey_field"]),
            vec_field=obj["vec_field"],
            vec_struct_field=list(
                map(
                    lambda item: types.foo_struct.FooStruct.from_json(item),
                    obj["vec_struct_field"],
                )
            ),
            option_field=obj["option_field"],
            option_struct_field=(
                None
                if obj["option_struct_field"] is None
                else types.foo_struct.FooStruct.from_json(obj["option_struct_field"])
            ),
            struct_field=types.foo_struct.FooStruct.from_json(obj["struct_field"]),
            array_field=obj["array_field"],
            enum_field1=types.foo_enum.from_json(obj["enum_field1"]),
            enum_field2=types.foo_enum.from_json(obj["enum_field2"]),
            enum_field3=types.foo_enum.from_json(obj["enum_field3"]),
            enum_field4=types.foo_enum.from_json(obj["enum_field4"]),
        )
