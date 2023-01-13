"""Mimics anchor/tests/composite/tests/composite.js."""
from anchorpy import Context, Program
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType
from pytest import fixture, mark
from pytest_asyncio import fixture as async_fixture
from solders.keypair import Keypair
from solders.sysvar import RENT

workspace = workspace_fixture(
    "anchor/tests/composite/", build_cmd="anchor build --skip-lint"
)


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    """Create a Program instance."""
    return workspace["composite"]


@async_fixture(scope="module")
async def initialized_accounts(program: Program) -> tuple[Keypair, Keypair]:
    """Generate keypairs and use them when callling the initialize function."""
    dummy_a = Keypair()
    dummy_b = Keypair()
    await program.rpc["initialize"](
        ctx=Context(
            accounts={
                "dummy_a": dummy_a.pubkey(),
                "dummy_b": dummy_b.pubkey(),
                "rent": RENT,
            },
            signers=[dummy_a, dummy_b],
            pre_instructions=[
                await program.account["DummyA"].create_instruction(dummy_a),
                await program.account["DummyB"].create_instruction(dummy_b),
            ],
        ),
    )
    return dummy_a, dummy_b


@async_fixture(scope="module")
async def composite_updated_accounts(
    program: Program,
    initialized_accounts: tuple[Keypair, Keypair],
) -> tuple[Keypair, Keypair]:
    """Run composite_update and return the keypairs used."""
    dummy_a, dummy_b = initialized_accounts
    ctx = Context(
        accounts={
            "foo": {"dummy_a": dummy_a.pubkey()},
            "bar": {"dummy_b": dummy_b.pubkey()},
        },
    )
    await program.rpc["composite_update"](1234, 4321, ctx=ctx)
    return initialized_accounts


@mark.asyncio
async def test_composite_update(
    program: Program,
    composite_updated_accounts: tuple[Keypair, Keypair],
) -> None:
    """Test that the call to composite_update worked."""
    dummy_a, dummy_b = composite_updated_accounts
    dummy_a_account = await program.account["DummyA"].fetch(dummy_a.pubkey())
    dummy_b_account = await program.account["DummyB"].fetch(dummy_b.pubkey())
    assert dummy_a_account.data == 1234
    assert dummy_b_account.data == 4321
