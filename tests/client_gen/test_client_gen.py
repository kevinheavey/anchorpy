from pathlib import Path
import json
import asyncio
from filecmp import dircmp
import subprocess
from pytest import fixture, mark
from pytest_asyncio import fixture as async_fixture
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solana.sysvar import SYSVAR_RENT_PUBKEY, SYSVAR_CLOCK_PUBKEY
from solana.system_program import SYS_PROGRAM_ID
from solana.rpc.commitment import Processed
from anchorpy.pytest_plugin import localnet_fixture
from anchorpy import Provider, Wallet
from tests.client_gen.example_program_gen.instructions import initialize
from tests.client_gen.example_program_gen.accounts import State

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
    res = await State.fetch(provider.connection, state.public_key)
    assert res is not None
    assert res.bool_field is True
    breakpoint()