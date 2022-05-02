from pathlib import Path
import json
import asyncio
from filecmp import dircmp
import subprocess
from pytest import fixture, mark
from pytest_asyncio import fixture as async_fixture
from construct import ListContainer
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solana.sysvar import SYSVAR_RENT_PUBKEY, SYSVAR_CLOCK_PUBKEY
from solana.system_program import SYS_PROGRAM_ID
from solana.rpc.commitment import Processed
from solana.publickey import PublicKey
from anchorpy.pytest_plugin import localnet_fixture
from anchorpy import Provider, Wallet
from tests.client_gen.example_program_gen.instructions import initialize
from tests.client_gen.example_program_gen.accounts import State
from tests.client_gen.example_program_gen.types import FooStruct, BarStruct
from tests.client_gen.example_program_gen.types.foo_enum import Named, Unnamed, NoFields, Struct

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
async def provider(localnet, payer: Keypair) -> Provider:
    wallet = Wallet(payer)
    conn = AsyncClient(commitment=Processed)
    prov = Provider(conn, wallet)
    yield prov
    await prov.close()


@fixture(scope="session")
def project_parent_dir(tmpdir_factory) -> Path:
    return Path(tmpdir_factory.mktemp("temp"))


@fixture(scope="session")
def project_dir(project_parent_dir: Path) -> Path:
    proj_dir = project_parent_dir / "tmp"
    subprocess.run(
        f"anchorpy client-gen ts-reference/tests/example-program-gen/idl.json {proj_dir} --program-id 3rTQ3R4B2PxZrAyx7EUefySPgZY8RhJf16cZajbmrzp8",
        shell=True, check=True)
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
    initialize_ix = initialize({"state": state.public_key, "payer": provider.wallet.public_key,
                                "nested": {"clock": SYSVAR_CLOCK_PUBKEY, "rent": SYSVAR_RENT_PUBKEY},
                                "system_program": SYS_PROGRAM_ID})
    tx = Transaction().add(initialize_ix)
    await provider.send(tx, [state, provider.wallet.payer])
    return state


@mark.asyncio
async def test_init_and_account_fetch(init_and_account_fetch: Keypair, provider: Provider) -> None:
    state = init_and_account_fetch
    vec_struct_field_enum_field_expected = Named(
                value={'bool_field': True, 'u8_field': 15, 'nested': BarStruct(some_field=True, other_field=10)})
    assert vec_struct_field_enum_field_expected.discriminator == 2
    assert vec_struct_field_enum_field_expected.kind == "Named"
    vec_struct_field_expected = [
        FooStruct(field1=123, field2=999, nested=BarStruct(some_field=True, other_field=10),
                  vec_nested=[BarStruct(some_field=True, other_field=10)],
                  option_nested=BarStruct(some_field=True, other_field=10), enum_field=vec_struct_field_enum_field_expected)]
    option_struct_field_expected = FooStruct(field1=123, field2=999,
                                             nested=BarStruct(some_field=True, other_field=10),
                                             vec_nested=[
                                                 BarStruct(some_field=True, other_field=10)],
                                             option_nested=BarStruct(some_field=True,
                                                                     other_field=10),
                                             enum_field=Named(
                                                 value={'bool_field': True, 'u8_field': 15,
                                                        'nested': BarStruct(some_field=True,
                                                                            other_field=10)}))
    struct_field_expected = FooStruct(field1=123, field2=999, nested=BarStruct(some_field=True, other_field=10),
                                      vec_nested=[BarStruct(some_field=True, other_field=10)],
                                      option_nested=BarStruct(some_field=True, other_field=10), enum_field=Named(
            value={'bool_field': True, 'u8_field': 15,
                   'nested': BarStruct(some_field=True, other_field=10)}))
    array_field_expected = ListContainer([True, False, True])
    vec_field_expected = ListContainer([1, 2, 100, 1000, 18446744073709551615])
    enum_field1_expected = Unnamed(value=(False, 10, BarStruct(some_field=True, other_field=10)))
    assert enum_field1_expected.kind == "Unnamed"
    assert enum_field1_expected.discriminator == 0
    enum_field2_expected = Named(value={'bool_field': True, 'u8_field': 20,
                                        'nested': BarStruct(some_field=True, other_field=10)})
    assert enum_field2_expected.kind == "Named"
    assert enum_field2_expected.discriminator == 2
    enum_field3_expected = Struct(value=(BarStruct(some_field=True, other_field=10),))
    assert enum_field3_expected.discriminator == 3
    assert enum_field3_expected.kind == "Struct"
    enum_field4_expected = NoFields()
    assert enum_field4_expected.discriminator == 6
    assert enum_field4_expected.kind == "NoFields"
    expected = State(bool_field=True, u8_field=234, i8_field=-123, u16_field=62345, i16_field=-31234,
                     u32_field=1234567891, i32_field=-1234567891, f32_field=123456.5, u64_field=9223372036854775817,
                     i64_field=-4611686018427387914, f64_field=1234567891.345,
                     u128_field=170141183460469231731687303715884105737,
                     i128_field=-85070591730234615865843651857942052874, bytes_field=b'\x01\x02\xff\xfe',
                     string_field='hello', pubkey_field=PublicKey("EPZP2wrcRtMxrAPJCXVEQaYD9eH7fH7h12YqKDcd4aS7"),
                     vec_field=vec_field_expected, vec_struct_field=vec_struct_field_expected,
                     option_field=None, option_struct_field=option_struct_field_expected,
                     struct_field=struct_field_expected,
                     array_field=array_field_expected,
                     enum_field1=enum_field1_expected,
                     enum_field2=enum_field2_expected,
                     enum_field3=enum_field3_expected, enum_field4=enum_field4_expected)
    res = await State.fetch(provider.connection, state.public_key)
    assert res == expected
