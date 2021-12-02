"""Mimics anchor/tests/errors/tests/events.js.

Note: this is unfinished.
"""
from typing import cast
import asyncio
from pytest import mark, fixture
from jsonrpcclient import Ok
from solana.rpc.websocket_api import connect, SolanaWsClientProtocol
from solana.rpc.request_builder import LogsSubscribeFilter
from anchorpy import (
    Program,
    EventParser,
)
from solana.rpc.responses import LogsNotification
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType


workspace = workspace_fixture("anchor/tests/events/")


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    return workspace["events"]


@mark.asyncio
async def test_initialize(program: Program) -> None:
    async with connect() as websocket:  # type: ignore
        ws = cast(SolanaWsClientProtocol, websocket)
        await ws.logs_subscribe(LogsSubscribeFilter.mentions(program.program_id))
        first_resp = await ws.recv()
        subscription_id = cast(Ok, first_resp).result
        await program.rpc["initialize"]()
        received = await ws.recv()
        received_cast = cast(LogsNotification, received)
        logs = received_cast.result.value.logs
        parser = EventParser(program.program_id, program.coder)
        parsed = parser.parse_logs(logs)
        event = parsed[0]
        assert event.data.data == 5
        assert event.data.label == "hello"
        await ws.logs_unsubscribe(subscription_id)


@mark.asyncio
async def test_multiple_events(program: Program) -> None:
    await asyncio.sleep(2)
    async with connect() as websocket:  # type: ignore
        ws = cast(SolanaWsClientProtocol, websocket)
        await ws.logs_subscribe(LogsSubscribeFilter.mentions(program.program_id))
        first_resp = await ws.recv()
        subscription_id = cast(Ok, first_resp).result
        await program.rpc["initialize"]()
        await program.rpc["test_event"]()
        parser = EventParser(program.program_id, program.coder)
        counter = 0
        async for message in ws:
            msg = cast(LogsNotification, message)
            logs = msg.result.value.logs
            parsed = parser.parse_logs(logs)
            event = parsed[0]
            counter += 1
            if counter == 1:
                assert event.data.data == 5
                assert event.data.label == "hello"
            if counter == 3:
                assert event.data.data == 6
                assert event.data.label == "bye"
            if counter == 4:
                break
        await ws.logs_unsubscribe(subscription_id)
