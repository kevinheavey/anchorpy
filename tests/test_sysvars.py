"""Mimics anchor/tests/sysvars."""
from pathlib import Path

from anchorpy.program.context import Context
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType
from pytest import mark
from solders.sysvar import (
    CLOCK,
    RENT,
    SYSVAR_STAKE_HISTORY_PUBKEY,
)

PATH = Path("anchor/tests/sysvars")


workspace = workspace_fixture(
    "anchor/tests/sysvars", build_cmd="anchor build --skip-lint"
)


@mark.asyncio
async def test_init(workspace: WorkspaceType) -> None:
    """Test that the initialize function is invoked successfully."""
    program = workspace["sysvars"]
    res = await program.rpc["sysvars"](
        ctx=Context(
            accounts={
                "clock": CLOCK,
                "rent": RENT,
                "stake_history": SYSVAR_STAKE_HISTORY_PUBKEY,
            }
        )
    )
    assert res
