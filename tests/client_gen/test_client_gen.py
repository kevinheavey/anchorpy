import asyncio
import json
from pathlib import Path
from typing import AsyncGenerator, List

from anchorpy import Provider, Wallet
from anchorpy.pytest_plugin import localnet_fixture
from construct import ListContainer
from pytest import fixture, mark
from pytest_asyncio import fixture as async_fixture
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Processed
from solana.rpc.core import RPCException
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction

from tests.client_gen.example_program_gen.accounts import State, State2
from tests.client_gen.example_program_gen.errors import from_tx_error
from tests.client_gen.example_program_gen.errors.custom import SomeError
from tests.client_gen.example_program_gen.instructions import (
    InitializeWithValuesAccounts,
    InitializeWithValuesArgs,
    cause_error,
    initialize,
    initialize_with_values,
    initialize_with_values2,
)
from tests.client_gen.example_program_gen.program_id import PROGRAM_ID
from tests.client_gen.example_program_gen.types import BarStruct, FooStruct
from tests.client_gen.example_program_gen.types.foo_enum import (
    Named,
    NoFields,
    Struct,
    Unnamed,
)

EXAMPLE_PROGRAM_DIR = Path("tests/client_gen/example-program")


@fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


localnet = localnet_fixture(EXAMPLE_PROGRAM_DIR, scope="session")


@fixture(scope="session")
def payer(localnet) -> Keypair:
    with (EXAMPLE_PROGRAM_DIR / ".anchor/test-ledger/faucet-keypair.json").open() as f:
        faucet_keypair_json: List[int] = json.load(f)
    return Keypair.from_bytes(faucet_keypair_json)


@async_fixture(scope="session")
async def provider(localnet, payer: Keypair) -> AsyncGenerator[Provider, None]:
    wallet = Wallet(payer)
    conn = AsyncClient(commitment=Processed)
    prov = Provider(conn, wallet)
    yield prov
    await prov.close()


@async_fixture(scope="session")
async def blockhash(provider: Provider) -> Hash:
    return (await provider.connection.get_latest_blockhash(Confirmed)).value.blockhash


@async_fixture(scope="module")
async def init_and_account_fetch(provider: Provider, blockhash: Hash) -> Keypair:
    state = Keypair()
    initialize_ix = initialize(
        {
            "state": state.pubkey(),
            "payer": provider.wallet.public_key,
        }
    )
    msg = Message.new_with_blockhash(
        [initialize_ix], provider.wallet.public_key, blockhash
    )
    tx = VersionedTransaction(msg, [provider.wallet.payer, state])
    await provider.send(tx)
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
        pubkey_field=Pubkey.from_string("EPZP2wrcRtMxrAPJCXVEQaYD9eH7fH7h12YqKDcd4aS7"),
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
    res = await State.fetch(provider.connection, state.pubkey())
    assert res == expected
    res = await State.fetch(provider.connection, state.pubkey(), program_id=PROGRAM_ID)
    assert res == expected


@async_fixture(scope="session")
async def setup_fetch_multiple(
    provider: Provider, blockhash: Hash
) -> tuple[Keypair, Keypair]:
    state = Keypair()
    another_state = Keypair()
    initialize_ixs = [
        initialize(
            {
                "state": state.pubkey(),
                "payer": provider.wallet.public_key,
            }
        ),
        initialize(
            {
                "state": another_state.pubkey(),
                "payer": provider.wallet.public_key,
            }
        ),
    ]
    msg = Message.new_with_blockhash(
        initialize_ixs, provider.wallet.public_key, blockhash
    )
    tx = VersionedTransaction(msg, [provider.wallet.payer, state, another_state])
    await provider.send(tx)
    return state, another_state


@mark.asyncio
async def test_fetch_multiple(
    provider: Provider, setup_fetch_multiple: tuple[Keypair, Keypair]
) -> None:
    state, another_state = setup_fetch_multiple
    non_state = Keypair()
    res = await State.fetch_multiple(
        provider.connection,
        [state.pubkey(), non_state.pubkey(), another_state.pubkey()],
    )
    assert isinstance(res[0], State)
    assert res[1] is None
    assert isinstance(res[2], State)


@async_fixture(scope="session")
async def send_instructions_with_args(
    provider: Provider, blockhash
) -> tuple[Keypair, Keypair]:
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
        pubkey_field=Pubkey.from_string("GDddEKTjLBqhskzSMYph5o54VYLQfPCR3PoFqKHLJK6s"),
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
        state=state.pubkey(),
        payer=provider.wallet.public_key,
    )
    ix1 = initialize_with_values(
        initialize_with_values_args, initialize_with_values_accounts
    )
    ix2 = initialize_with_values2(
        {"vec_of_option": [None, None, 20]},
        {
            "state": state2.pubkey(),
            "payer": provider.wallet.public_key,
        },
    )
    msg = Message.new_with_blockhash([ix1, ix2], provider.wallet.public_key, blockhash)
    tx = VersionedTransaction(msg, [provider.wallet.payer, state, state2])
    await provider.send(tx)
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
        pubkey_field=Pubkey.from_string("GDddEKTjLBqhskzSMYph5o54VYLQfPCR3PoFqKHLJK6s"),
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
    res = await State.fetch(provider.connection, state.pubkey())
    res2 = await State2.fetch(provider.connection, state2.pubkey())
    assert res == expected
    assert res2 == expected2


@mark.asyncio
async def test_cause_error(provider: Provider, blockhash: Hash) -> None:
    msg = Message.new_with_blockhash(
        [cause_error()], provider.wallet.public_key, blockhash
    )
    tx = VersionedTransaction(msg, [provider.wallet.payer])
    try:
        await provider.send(tx)
    except RPCException as exc:
        caught = from_tx_error(exc)
        assert isinstance(caught, SomeError)
