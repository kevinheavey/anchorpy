"""Mimics anchor/tests/errors/tests/events.js.

Note: this is unfinished.
"""
import asyncio
import json
from pathlib import Path
import websockets
from pytest import mark, fixture
from anchorpy import (
    Program,
    create_workspace,
    close_workspace,
    EventParser,
)
from tests.utils import get_localnet

PATH = Path("anchor/tests/events/")

localnet = get_localnet(PATH)


@fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@fixture(scope="module")
async def program(localnet) -> Program:
    workspace = create_workspace(PATH)
    yield workspace["events"]
    await close_workspace(workspace)


@mark.asyncio
async def test_initialize(program: Program) -> None:
    uri = "ws://127.0.0.1:8900"
    async with websockets.connect(uri) as websocket:  # type: ignore
        await websocket.send(
            '{"jsonrpc": "2.0", "id": 1, "method": "logsSubscribe", "params": ["all"]}'
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
        assert event["data"]["data"] == 5
        assert event["data"]["label"] == "hello"
