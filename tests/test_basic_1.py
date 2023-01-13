"""Mimics anchor/examples/tutorial/basic-1."""

from anchorpy import Context, Program
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType
from pytest import fixture, mark
from pytest_asyncio import fixture as async_fixture
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID

workspace = workspace_fixture(
    "anchor/examples/tutorial/basic-1", build_cmd="anchor build --skip-lint"
)


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    """Create a Program instance."""
    return workspace["basic_1"]


@async_fixture(scope="module")
async def initialized_account(program: Program) -> Keypair:
    """Generate a keypair and initialize it."""
    my_account = Keypair()
    await program.rpc["initialize"](
        1234,
        ctx=Context(
            accounts={
                "my_account": my_account.pubkey(),
                "user": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[my_account],
        ),
    )
    return my_account


@mark.asyncio
async def test_create_and_initialize_account(
    program: Program,
    initialized_account: Keypair,
) -> None:
    """Test creating and initializing account in single tx."""
    account = await program.account["MyAccount"].fetch(initialized_account.pubkey())
    assert account.data == 1234


@mark.asyncio
async def test_update_previously_created_account(
    initialized_account: Keypair,
    program: Program,
) -> None:
    """Test updating a previously created account."""
    await program.rpc["update"](
        4321,
        ctx=Context(accounts={"my_account": initialized_account.pubkey()}),
    )
    account = await program.account["MyAccount"].fetch(initialized_account.pubkey())
    assert account.data == 4321
