"""Mimics anchor/tests/sysvars."""
from pathlib import Path

from pytest import mark
from solana.sysvar import (
    SYSVAR_CLOCK_PUBKEY,
    SYSVAR_RENT_PUBKEY,
    SYSVAR_STAKE_HISTORY_PUBKEY,
)

from anchorpy.program.context import Context
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType

PATH = Path("anchor/tests/sysvars")


workspace = workspace_fixture("anchor/tests/sysvars")


@mark.asyncio
async def test_init(workspace: WorkspaceType) -> None:
    """Test that the initialize function is invoked successfully."""
    program = workspace["sysvars"]
    res = await program.rpc["sysvars"](
        ctx=Context(
            accounts={
                "clock": SYSVAR_CLOCK_PUBKEY,
                "rent": SYSVAR_RENT_PUBKEY,
                "stake_history": SYSVAR_STAKE_HISTORY_PUBKEY,
            }
        )
    )
    assert res
