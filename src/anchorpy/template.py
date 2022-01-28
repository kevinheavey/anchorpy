# noqa: D100
INIT_TESTS = '''"""AnchorPy integration tests."""
import asyncio
from pytest import fixture, mark

from anchorpy import Program
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType


@fixture(scope="module")
def event_loop():
    """Create a module-scoped event loop so we can use module-scope async fixtures."""
    loop = asyncio.get_event_loop_policy().new_event_loop()  # noqa: DAR301
    yield loop
    loop.close()


workspace = workspace_fixture(".")


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    """Create a Program instance."""
    return workspace["{}"]


@mark.asyncio
async def test_init(program: Program) -> None:
    """Test that the initialize function is invoked successfully."""
    await program.rpc["initialize"]()
'''
