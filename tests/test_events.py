"""Mimics anchor/tests/errors/tests/events.js.

Note: this is unfinished.
"""
import json
import websockets
from pytest import mark, fixture
from anchorpy import (
    Program,
    EventParser,
)
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType


workspace = workspace_fixture("anchor/tests/events/")


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    return workspace["events"]


@mark.asyncio
async def test_initialize(program: Program) -> None:
    uri = "ws://127.0.0.1:8900"
    async with websockets.connect(uri) as websocket:  # type: ignore
        await websocket.send(
            '{"jsonrpc": "2.0", "id": 1, "method": "logsSubscribe", "params": ["all"]}',
        )
        received = await websocket.recv()
        await program.rpc["initialize"]()
        received = await websocket.recv()
        as_json = json.loads(received)
        logs = as_json["params"]["result"]["value"]["logs"]
        parser = EventParser(program.program_id, program.coder)
        parsed = []
        parser.parse_logs(logs, lambda evt: parsed.append(evt))
        event = parsed[0]
        assert event.data.data == 5
        assert event.data.label == "hello"
