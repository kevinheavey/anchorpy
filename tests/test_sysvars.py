"""Mimics anchor/tests/sysvars."""
from pathlib import Path

from pytest import mark
from solana.sysvar import (
    SYSVAR_CLOCK_PUBKEY,
    SYSVAR_RENT_PUBKEY,
    SYSVAR_STAKE_HISTORY_PUBKEY,
)

from anchorpy import create_workspace
from anchorpy.program.context import Context
from anchorpy.pytest_plugin import get_localnet

PATH = Path("anchor/tests/sysvars")


localnet = get_localnet(PATH)


@mark.asyncio
async def test_init(localnet) -> None:
    """Test that the initialize function is invoked successfully."""
    workspace = create_workspace(PATH)
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
    await program.close()
