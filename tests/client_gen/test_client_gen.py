from pathlib import Path
from typing import AsyncGenerator
import json
import asyncio
from filecmp import dircmp
import subprocess
from pytest import fixture, mark
from py.path import local
from pytest_asyncio import fixture as async_fixture
from construct import ListContainer
from solders.rpc.errors import SendTransactionPreflightFailureMessage
from solders.rpc.responses import SimulateTransactionResp
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solana.sysvar import SYSVAR_RENT_PUBKEY, SYSVAR_CLOCK_PUBKEY
from solana.system_program import SYS_PROGRAM_ID
from solana.rpc.commitment import Processed
from solana.rpc.core import RPCException
from solana.publickey import PublicKey
from anchorpy.pytest_plugin import localnet_fixture
from anchorpy import Provider, Wallet
from anchorpy.cli import client_gen
from tests.client_gen.example_program_gen.instructions import (
    initialize,
    initialize_with_values,
    initialize_with_values2,
    InitializeWithValuesAccounts,
    InitializeWithValuesArgs,
    cause_error,
)
from tests.client_gen.example_program_gen.accounts import State, State2
from tests.client_gen.example_program_gen.program_id import PROGRAM_ID
from tests.client_gen.example_program_gen.types import FooStruct, BarStruct
from tests.client_gen.example_program_gen.types.foo_enum import (
    Named,
    NamedValue,
    Unnamed,
    NoFields,
    Struct,
)
from tests.client_gen.example_program_gen.errors import from_tx_error  # noqa: WPS347
from tests.client_gen.example_program_gen.errors.custom import SomeError
from tests.client_gen.example_program_gen.errors.anchor import InvalidProgramId

EXAMPLE_PROGRAM_DIR = Path("ts-reference/tests/example-program")


@fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()  # noqa: DAR301
    yield loop
    loop.close()


localnet = localnet_fixture(EXAMPLE_PROGRAM_DIR, scope="session")


@fixture(scope="session")
def payer(localnet) -> Keypair:
    with (EXAMPLE_PROGRAM_DIR / ".anchor/test-ledger/faucet-keypair.json").open() as f:
        faucet_keypair_json = json.load(f)
    return Keypair.from_secret_key(bytes(faucet_keypair_json))


@async_fixture(scope="session")
async def provider(localnet, payer: Keypair) -> AsyncGenerator[Provider, None]:
    wallet = Wallet(payer)
    conn = AsyncClient(commitment=Processed)
    prov = Provider(conn, wallet)
    yield prov
    await prov.close()


@fixture(scope="session")
def project_parent_dir(tmpdir_factory) -> Path:
    return Path(tmpdir_factory.mktemp("temp"))


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


@fixture(scope="session")
def project_dir(project_parent_dir: Path) -> Path:
    proj_dir = project_parent_dir / "tmp"
    subprocess.run(
        f"anchorpy client-gen ts-reference/tests/example-program-gen/idl.json {proj_dir} --program-id 3rTQ3R4B2PxZrAyx7EUefySPgZY8RhJf16cZajbmrzp8",
        shell=True,
        check=True,
    )
    return proj_dir


def has_differences(dcmp: dircmp) -> bool:
    differences = dcmp.left_only + dcmp.right_only + dcmp.diff_files
    if differences:
        return True
    return any([has_differences(subdcmp) for subdcmp in dcmp.subdirs.values()])


def test_generated_as_expected(project_dir: Path) -> None:
    dcmp = dircmp(project_dir, "tests/client_gen/example_program_gen")
    assert not has_differences(dcmp)


@async_fixture(scope="module")
async def init_and_account_fetch(provider: Provider) -> Keypair:
    state = Keypair()
    initialize_ix = initialize(
        {
            "state": state.public_key,
            "payer": provider.wallet.public_key,
            "nested": {"clock": SYSVAR_CLOCK_PUBKEY, "rent": SYSVAR_RENT_PUBKEY},
            "system_program": SYS_PROGRAM_ID,
        }
    )
    tx = Transaction().add(initialize_ix)
    await provider.send(tx, [state, provider.wallet.payer])
    return state


@mark.asyncio
async def test_init_and_account_fetch(
    init_and_account_fetch: Keypair, provider: Provider
) -> None:
    state = init_and_account_fetch
    vec_struct_field_enum_field_expected = Named(
        value={
            "bool_field": True,
            "u8_field": 15,
            "nested": BarStruct(some_field=True, other_field=10),
        }
    )
    assert vec_struct_field_enum_field_expected.discriminator == 2
    assert vec_struct_field_enum_field_expected.kind == "Named"
    vec_struct_field_expected = [
        FooStruct(
            field1=123,
            field2=999,
            nested=BarStruct(some_field=True, other_field=10),
            vec_nested=[BarStruct(some_field=True, other_field=10)],
            option_nested=BarStruct(some_field=True, other_field=10),
            enum_field=vec_struct_field_enum_field_expected,
        )
    ]
    option_struct_field_expected = FooStruct(
        field1=123,
        field2=999,
        nested=BarStruct(some_field=True, other_field=10),
        vec_nested=[BarStruct(some_field=True, other_field=10)],
        option_nested=BarStruct(some_field=True, other_field=10),
        enum_field=Named(
            value={
                "bool_field": True,
                "u8_field": 15,
                "nested": BarStruct(some_field=True, other_field=10),
            }
        ),
    )
    struct_field_expected = FooStruct(
        field1=123,
        field2=999,
        nested=BarStruct(some_field=True, other_field=10),
        vec_nested=[BarStruct(some_field=True, other_field=10)],
        option_nested=BarStruct(some_field=True, other_field=10),
        enum_field=Named(
            value={
                "bool_field": True,
                "u8_field": 15,
                "nested": BarStruct(some_field=True, other_field=10),
            }
        ),
    )
    array_field_expected = ListContainer([True, False, True])
    vec_field_expected = ListContainer([1, 2, 100, 1000, 18446744073709551615])
    enum_field1_expected = Unnamed(
        value=(False, 10, BarStruct(some_field=True, other_field=10))
    )
    assert enum_field1_expected.kind == "Unnamed"
    assert enum_field1_expected.discriminator == 0
    enum_field2_expected = Named(
        value={
            "bool_field": True,
            "u8_field": 20,
            "nested": BarStruct(some_field=True, other_field=10),
        }
    )
    assert enum_field2_expected.kind == "Named"
    assert enum_field2_expected.discriminator == 2
    enum_field3_expected = Struct(value=(BarStruct(some_field=True, other_field=10),))
    assert enum_field3_expected.discriminator == 3
    assert enum_field3_expected.kind == "Struct"
    enum_field4_expected = NoFields()
    assert enum_field4_expected.discriminator == 6
    assert enum_field4_expected.kind == "NoFields"
    expected = State(
        bool_field=True,
        u8_field=234,
        i8_field=-123,
        u16_field=62345,
        i16_field=-31234,
        u32_field=1234567891,
        i32_field=-1234567891,
        f32_field=123456.5,
        u64_field=9223372036854775817,
        i64_field=-4611686018427387914,
        f64_field=1234567891.345,
        u128_field=170141183460469231731687303715884105737,
        i128_field=-85070591730234615865843651857942052874,
        bytes_field=b"\x01\x02\xff\xfe",
        string_field="hello",
        pubkey_field=PublicKey("EPZP2wrcRtMxrAPJCXVEQaYD9eH7fH7h12YqKDcd4aS7"),
        vec_field=vec_field_expected,
        vec_struct_field=vec_struct_field_expected,
        option_field=None,
        option_struct_field=option_struct_field_expected,
        struct_field=struct_field_expected,
        array_field=array_field_expected,
        enum_field1=enum_field1_expected,
        enum_field2=enum_field2_expected,
        enum_field3=enum_field3_expected,
        enum_field4=enum_field4_expected,
    )
    res = await State.fetch(provider.connection, state.public_key)
    assert res == expected
    res = await State.fetch(
        provider.connection, state.public_key, program_id=PROGRAM_ID
    )
    assert res == expected


@async_fixture(scope="session")
async def setup_fetch_multiple(provider: Provider) -> tuple[Keypair, Keypair]:
    state = Keypair()
    another_state = Keypair()
    initialize_ixs = [
        initialize(
            {
                "state": state.public_key,
                "payer": provider.wallet.public_key,
                "nested": {"clock": SYSVAR_CLOCK_PUBKEY, "rent": SYSVAR_RENT_PUBKEY},
                "system_program": SYS_PROGRAM_ID,
            }
        ),
        initialize(
            {
                "state": another_state.public_key,
                "payer": provider.wallet.public_key,
                "nested": {"clock": SYSVAR_CLOCK_PUBKEY, "rent": SYSVAR_RENT_PUBKEY},
                "system_program": SYS_PROGRAM_ID,
            }
        ),
    ]
    tx = Transaction().add(*initialize_ixs)
    await provider.send(tx, [state, another_state])
    return state, another_state


@mark.asyncio
async def test_fetch_multiple(
    provider: Provider, setup_fetch_multiple: tuple[Keypair, Keypair]
) -> None:
    state, another_state = setup_fetch_multiple
    non_state = Keypair()
    res = await State.fetch_multiple(
        provider.connection,
        [state.public_key, non_state.public_key, another_state.public_key],
    )
    assert isinstance(res[0], State)
    assert res[1] is None
    assert isinstance(res[2], State)


@async_fixture(scope="session")
async def send_instructions_with_args(provider: Provider) -> tuple[Keypair, Keypair]:
    state = Keypair()
    state2 = Keypair()
    vec_struct_field = [
        FooStruct(
            field1=1,
            field2=2,
            nested=BarStruct(some_field=True, other_field=55),
            vec_nested=[BarStruct(some_field=False, other_field=11)],
            option_nested=None,
            enum_field=Unnamed((True, 22, BarStruct(some_field=True, other_field=33))),
        )
    ]
    struct_field = FooStruct(
        field1=1,
        field2=2,
        nested=BarStruct(some_field=True, other_field=55),
        vec_nested=[BarStruct(some_field=False, other_field=11)],
        option_nested=None,
        enum_field=NoFields(),
    )
    enum_field1 = Unnamed((True, 15, BarStruct(some_field=False, other_field=200)))
    enum_field2 = Named(
        {
            "bool_field": True,
            "u8_field": 128,
            "nested": BarStruct(some_field=False, other_field=1),
        }
    )
    enum_field3 = Struct((BarStruct(some_field=True, other_field=15),))
    initialize_with_values_args = InitializeWithValuesArgs(
        bool_field=True,
        u8_field=253,
        i8_field=-120,
        u16_field=61234,
        i16_field=-31253,
        u32_field=1234567899,
        i32_field=-123456789,
        f32_field=123458.5,
        u64_field=9223372036854775810,
        i64_field=-4611686018427387912,
        f64_field=1234567892.445,
        u128_field=170141183460469231731687303715884105740,
        i128_field=-85070591730234615865843651857942052877,
        bytes_field=bytes([5, 10, 255]),
        string_field="string value",
        pubkey_field=PublicKey("GDddEKTjLBqhskzSMYph5o54VYLQfPCR3PoFqKHLJK6s"),
        vec_field=[1, 123456789123456789],
        vec_struct_field=vec_struct_field,
        option_field=True,
        option_struct_field=None,
        struct_field=struct_field,
        array_field=[True, True, False],
        enum_field1=enum_field1,
        enum_field2=enum_field2,
        enum_field3=enum_field3,
        enum_field4=NoFields(),
    )
    initialize_with_values_accounts = InitializeWithValuesAccounts(
        state=state.public_key,
        nested={"clock": SYSVAR_CLOCK_PUBKEY, "rent": SYSVAR_RENT_PUBKEY},
        payer=provider.wallet.public_key,
        system_program=SYS_PROGRAM_ID,
    )
    ix1 = initialize_with_values(
        initialize_with_values_args, initialize_with_values_accounts
    )
    ix2 = initialize_with_values2(
        {"vec_of_option": [None, None, 20]},
        {
            "state": state2.public_key,
            "payer": provider.wallet.public_key,
            "system_program": SYS_PROGRAM_ID,
        },
    )
    tx = Transaction().add(ix1, ix2)
    await provider.send(tx, [state, state2, provider.wallet.payer])
    return state, state2


@mark.asyncio
async def test_instructions_with_args(
    send_instructions_with_args: tuple[Keypair, Keypair], provider: Provider
) -> None:
    state, state2 = send_instructions_with_args
    expected = State(
        bool_field=True,
        u8_field=253,
        i8_field=-120,
        u16_field=61234,
        i16_field=-31253,
        u32_field=1234567899,
        i32_field=-123456789,
        f32_field=123458.5,
        u64_field=9223372036854775810,
        i64_field=-4611686018427387912,
        f64_field=1234567892.445,
        u128_field=170141183460469231731687303715884105740,
        i128_field=-85070591730234615865843651857942052877,
        bytes_field=b"\x05\n\xff",
        string_field="string value",
        pubkey_field=PublicKey("GDddEKTjLBqhskzSMYph5o54VYLQfPCR3PoFqKHLJK6s"),
        vec_field=ListContainer([1, 123456789123456789]),
        vec_struct_field=[
            FooStruct(
                field1=1,
                field2=2,
                nested=BarStruct(some_field=True, other_field=55),
                vec_nested=[BarStruct(some_field=False, other_field=11)],
                option_nested=None,
                enum_field=Unnamed(
                    value=(True, 22, BarStruct(some_field=True, other_field=33))
                ),
            )
        ],
        option_field=True,
        option_struct_field=None,
        struct_field=FooStruct(
            field1=1,
            field2=2,
            nested=BarStruct(some_field=True, other_field=55),
            vec_nested=[BarStruct(some_field=False, other_field=11)],
            option_nested=None,
            enum_field=NoFields(),
        ),
        array_field=ListContainer([True, True, False]),
        enum_field1=Unnamed(
            value=(True, 15, BarStruct(some_field=False, other_field=200))
        ),
        enum_field2=Named(
            value={
                "bool_field": True,
                "u8_field": 128,
                "nested": BarStruct(some_field=False, other_field=1),
            }
        ),
        enum_field3=Struct(value=(BarStruct(some_field=True, other_field=15),)),
        enum_field4=NoFields(),
    )
    expected2 = State2(vec_of_option=ListContainer([None, None, 20]))
    res = await State.fetch(provider.connection, state.public_key)
    res2 = await State2.fetch(provider.connection, state2.public_key)
    assert res == expected
    assert res2 == expected2


@mark.asyncio
async def test_cause_error(provider: Provider) -> None:
    tx = Transaction().add(cause_error())
    try:
        await provider.send(tx, [provider.wallet.payer])
    except RPCException as exc:
        caught = from_tx_error(exc)
        assert isinstance(caught, SomeError)


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
        pubkey_field=PublicKey("EPZP2wrcRtMxrAPJCXVEQaYD9eH7fH7h12YqKDcd4aS7"),
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
