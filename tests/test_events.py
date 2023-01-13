"""Mimics anchor/tests/errors/tests/events.js.

Note: this is unfinished.
"""
from typing import cast

from anchorpy import (
    EventParser,
    Program,
)
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType
from pytest import fixture, mark
from solana.rpc.websocket_api import SolanaWsClientProtocol, connect
from solders.rpc.config import RpcTransactionLogsFilter
from solders.rpc.responses import LogsNotification

workspace = workspace_fixture(
    "anchor/tests/events/", build_cmd="anchor build --skip-lint"
)


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    return workspace["events"]


@mark.asyncio
async def test_initialize(program: Program) -> None:
    async with cast(SolanaWsClientProtocol, connect()) as websocket:  # type: ignore
        await websocket.logs_subscribe(RpcTransactionLogsFilter.All)
        await websocket.recv()
        await program.rpc["initialize"]()
        received = await websocket.recv()
        first = received[0]
        assert isinstance(first, LogsNotification)
        logs = first.result.value.logs
        parser = EventParser(program.program_id, program.coder)
        parsed = []
        parser.parse_logs(logs, lambda evt: parsed.append(evt))
        event = parsed[0]
        assert event.data.data == 5
        assert event.data.label == "hello"
