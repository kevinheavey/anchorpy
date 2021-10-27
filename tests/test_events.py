"""Mimics anchor/tests/errors/tests/events.js."""
import asyncio
from pathlib import Path
import websockets
from pytest import raises, mark, fixture
from anchorpy import ProgramError, Program, create_workspace, close_workspace, Context
from solana.keypair import Keypair
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.transaction import AccountMeta, Transaction, TransactionInstruction
from solana.rpc.core import RPCException
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
    yield workspace["errors"]
    await close_workspace(workspace)


@mark.asyncio
async def test_initialize(program: Program) -> None:
    uri = "http://127.0.0.1:8900"
    async with websockets.connect(uri) as websocket:
        await program.rpc["initialize"]()
        for message in websocket:
            print(message)
