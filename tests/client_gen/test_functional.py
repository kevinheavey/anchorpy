import json
from filecmp import dircmp
from pathlib import Path

from anchorpy.cli import client_gen
from py.path import local
from solana.rpc.core import RPCException
from solders.pubkey import Pubkey
from solders.rpc.errors import SendTransactionPreflightFailureMessage
from solders.rpc.responses import SimulateTransactionResp

from tests.client_gen.example_program_gen.accounts import State
from tests.client_gen.example_program_gen.errors import from_tx_error
from tests.client_gen.example_program_gen.errors.anchor import InvalidProgramId
from tests.client_gen.example_program_gen.types import BarStruct, FooStruct
from tests.client_gen.example_program_gen.types.foo_enum import (
    Named,
    NamedValue,
    NoFields,
    Struct,
    Unnamed,
)


def test_quarry_mine(tmpdir: local) -> None:
    proj_dir = Path(tmpdir)
    out_dir = proj_dir / "generated"
    idl_path = Path("tests/idls/quarry_mine.json")
    client_gen(idl_path, out_dir, "placeholder")


def test_merkle_distributor(tmpdir: local) -> None:
    proj_dir = Path(tmpdir)
    out_dir = proj_dir / "generated"
    idl_path = Path("tests/idls/merkle_distributor.json")
    client_gen(idl_path, out_dir, "placeholder")


def test_null_err_when_cpi_fails() -> None:
    to_dump = {
        "jsonrpc": "2.0",
        "error": {
            "code": -32002,
            "message": "",
            "data": {
                "err": {"InstructionError": [0, {"Custom": 3}]},
                "logs": [
                    "Program 3rTQ3R4B2PxZrAyx7EUefySPgZY8RhJf16cZajbmrzp8 invoke [1]",
                    "Program log: Instruction: CauseError",
                    "Program 11111111111111111111111111111111 invoke [2]",
                    "Allocate: requested 1000000000000000000, max allowed 10485760",
                    "Program 11111111111111111111111111111111 failed: custom program error: 0x3",
                    "Program 3rTQ3R4B2PxZrAyx7EUefySPgZY8RhJf16cZajbmrzp8 consumed 7958 of 1400000 compute units",
                    "Program 3rTQ3R4B2PxZrAyx7EUefySPgZY8RhJf16cZajbmrzp8 failed: custom program error: 0x3",
                ],
            },
        },
    }
    raw = json.dumps(to_dump)
    parsed = SimulateTransactionResp.from_json(raw)
    assert isinstance(parsed, SendTransactionPreflightFailureMessage)
    err_mock = RPCException(parsed)
    assert from_tx_error(err_mock) is None


def test_parses_anchor_error() -> None:
    to_dump = {
        "jsonrpc": "2.0",
        "error": {
            "code": -32002,
            "message": "",
            "data": {
                "err": {"InstructionError": [0, {"Custom": 3008}]},
                "logs": [
                    "Program 3rTQ3R4B2PxZrAyx7EUefySPgZY8RhJf16cZajbmrzp8 invoke [1]",
                    "Program log: Instruction: CauseError",
                    "Program log: AnchorError caused by account: system_program. Error Code: InvalidProgramId. Error Number: 3008. Error Message: Program ID was not as expected.",
                    "Program log: Left:",
                    "Program log: 24S58Cp5Myf6iGx4umBNd7RgDrZ9nkKzvkfFHBMDomNa",
                    "Program log: Right:",
                    "Program log: 11111111111111111111111111111111",
                    "Program 3rTQ3R4B2PxZrAyx7EUefySPgZY8RhJf16cZajbmrzp8 consumed 5043 of 1400000 compute units",
                    "Program 3rTQ3R4B2PxZrAyx7EUefySPgZY8RhJf16cZajbmrzp8 failed: custom program error: 0xbc0",
                ],
            },
        },
    }
    raw = json.dumps(to_dump)
    parsed = SimulateTransactionResp.from_json(raw)
    assert isinstance(parsed, SendTransactionPreflightFailureMessage)
    err_mock = RPCException(parsed)
    assert isinstance(from_tx_error(err_mock), InvalidProgramId)


def test_json() -> None:
    vec_struct_field = [
        FooStruct(
            field1=5,
            field2=6,
            nested=BarStruct(
                some_field=True,
                other_field=15,
            ),
            vec_nested=[
                BarStruct(
                    some_field=True,
                    other_field=13,
                ),
            ],
            option_nested=None,
            enum_field=Unnamed(
                (
                    False,
                    111,
                    BarStruct(
                        some_field=False,
                        other_field=11,
                    ),
                )
            ),
        ),
    ]
    option_struct_field = FooStruct(
        field1=8,
        field2=9,
        nested=BarStruct(
            some_field=True,
            other_field=17,
        ),
        vec_nested=[
            BarStruct(
                some_field=True,
                other_field=10,
            ),
        ],
        option_nested=BarStruct(
            some_field=False,
            other_field=99,
        ),
        enum_field=NoFields(),
    )
    struct_field = FooStruct(
        field1=11,
        field2=12,
        nested=BarStruct(
            some_field=False,
            other_field=177,
        ),
        vec_nested=[
            BarStruct(
                some_field=True,
                other_field=15,
            ),
        ],
        option_nested=BarStruct(
            some_field=True,
            other_field=75,
        ),
        enum_field=NoFields(),
    )
    enum_field1 = Unnamed(
        (
            False,
            157,
            BarStruct(
                some_field=True,
                other_field=193,
            ),
        )
    )
    enum_field2 = Named(
        NamedValue(
            bool_field=False,
            u8_field=77,
            nested=BarStruct(
                some_field=True,
                other_field=100,
            ),
        )
    )
    enum_field3 = Struct(
        (
            BarStruct(
                some_field=False,
                other_field=122,
            ),
        )
    )
    state = State(
        bool_field=True,
        u8_field=255,
        i8_field=-120,
        u16_field=62000,
        i16_field=-31000,
        u32_field=123456789,
        i32_field=-123456789,
        f32_field=123456.5,
        u64_field=9223372036854775805,
        i64_field=4611686018427387910,
        f64_field=1234567891.35,
        u128_field=170141183460469231731687303715884105760,
        i128_field=-85070591730234615865843651857942052897,
        bytes_field=bytes([1, 255]),
        string_field="a string",
        pubkey_field=Pubkey.from_string("EPZP2wrcRtMxrAPJCXVEQaYD9eH7fH7h12YqKDcd4aS7"),
        vec_field=[10, 1234567890123456],
        vec_struct_field=vec_struct_field,
        option_field=None,
        option_struct_field=option_struct_field,
        struct_field=struct_field,
        array_field=[True, False],
        enum_field1=enum_field1,
        enum_field2=enum_field2,
        enum_field3=enum_field3,
        enum_field4=NoFields(),
    )
    state_json = state.to_json()
    expected = {
        "bool_field": True,
        "u8_field": 255,
        "i8_field": -120,
        "u16_field": 62000,
        "i16_field": -31000,
        "u32_field": 123456789,
        "i32_field": -123456789,
        "f32_field": 123456.5,
        "u64_field": 9223372036854775805,
        "i64_field": 4611686018427387910,
        "f64_field": 1234567891.35,
        "u128_field": 170141183460469231731687303715884105760,
        "i128_field": -85070591730234615865843651857942052897,
        "bytes_field": [1, 255],
        "string_field": "a string",
        "pubkey_field": "EPZP2wrcRtMxrAPJCXVEQaYD9eH7fH7h12YqKDcd4aS7",
        "vec_field": [10, 1234567890123456],
        "vec_struct_field": [
            {
                "field1": 5,
                "field2": 6,
                "nested": {
                    "some_field": True,
                    "other_field": 15,
                },
                "vec_nested": [
                    {
                        "some_field": True,
                        "other_field": 13,
                    },
                ],
                "option_nested": None,
                "enum_field": {
                    "kind": "Unnamed",
                    "value": (
                        False,
                        111,
                        {
                            "some_field": False,
                            "other_field": 11,
                        },
                    ),
                },
            },
        ],
        "option_field": None,
        "option_struct_field": {
            "field1": 8,
            "field2": 9,
            "nested": {
                "some_field": True,
                "other_field": 17,
            },
            "vec_nested": [
                {
                    "some_field": True,
                    "other_field": 10,
                },
            ],
            "option_nested": {
                "some_field": False,
                "other_field": 99,
            },
            "enum_field": {
                "kind": "NoFields",
            },
        },
        "struct_field": {
            "field1": 11,
            "field2": 12,
            "nested": {
                "some_field": False,
                "other_field": 177,
            },
            "vec_nested": [
                {
                    "some_field": True,
                    "other_field": 15,
                },
            ],
            "option_nested": {
                "some_field": True,
                "other_field": 75,
            },
            "enum_field": {
                "kind": "NoFields",
            },
        },
        "array_field": [True, False],
        "enum_field1": {
            "kind": "Unnamed",
            "value": (
                False,
                157,
                {
                    "some_field": True,
                    "other_field": 193,
                },
            ),
        },
        "enum_field2": {
            "kind": "Named",
            "value": {
                "bool_field": False,
                "u8_field": 77,
                "nested": {
                    "some_field": True,
                    "other_field": 100,
                },
            },
        },
        "enum_field3": {
            "kind": "Struct",
            "value": (
                {
                    "some_field": False,
                    "other_field": 122,
                },
            ),
        },
        "enum_field4": {
            "kind": "NoFields",
        },
    }
    assert state_json == expected
    state_from_json = State.from_json(state_json)
    assert state_from_json == state


def has_differences(dcmp: dircmp) -> bool:
    differences = dcmp.left_only + dcmp.right_only + dcmp.diff_files
    if differences:
        return True
    return any([has_differences(subdcmp) for subdcmp in dcmp.subdirs.values()])


def test_generated_as_expected(project_dir: Path) -> None:
    dcmp = dircmp(project_dir, "tests/client_gen/example_program_gen")
    assert not has_differences(dcmp)
