from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT, CLOCK
from solders.instruction import Instruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
from construct import Construct
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class InitializeWithValuesArgs(typing.TypedDict):
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


layout = borsh.CStruct(
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


class InitializeWithValuesAccounts(typing.TypedDict):
    state: Pubkey
    payer: Pubkey


def initialize_with_values(
    args: InitializeWithValuesArgs,
    accounts: InitializeWithValuesAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=CLOCK, is_signer=False, is_writable=False),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xdcI\x08\xd5\xb2E\xb5\x8d"
    encoded_args = layout.build(
        {
            "bool_field": args["bool_field"],
            "u8_field": args["u8_field"],
            "i8_field": args["i8_field"],
            "u16_field": args["u16_field"],
            "i16_field": args["i16_field"],
            "u32_field": args["u32_field"],
            "i32_field": args["i32_field"],
            "f32_field": args["f32_field"],
            "u64_field": args["u64_field"],
            "i64_field": args["i64_field"],
            "f64_field": args["f64_field"],
            "u128_field": args["u128_field"],
            "i128_field": args["i128_field"],
            "bytes_field": args["bytes_field"],
            "string_field": args["string_field"],
            "pubkey_field": args["pubkey_field"],
            "vec_field": args["vec_field"],
            "vec_struct_field": list(
                map(lambda item: item.to_encodable(), args["vec_struct_field"])
            ),
            "option_field": args["option_field"],
            "option_struct_field": (
                None
                if args["option_struct_field"] is None
                else args["option_struct_field"].to_encodable()
            ),
            "struct_field": args["struct_field"].to_encodable(),
            "array_field": args["array_field"],
            "enum_field1": args["enum_field1"].to_encodable(),
            "enum_field2": args["enum_field2"].to_encodable(),
            "enum_field3": args["enum_field3"].to_encodable(),
            "enum_field4": args["enum_field4"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
