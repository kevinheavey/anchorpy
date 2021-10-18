import asyncio
from pathlib import Path
from typing import List, Tuple
import random
import string

from pytest import mark, fixture
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.system_program import SYS_PROGRAM_ID

from anchorpy import Program, create_workspace, Context, Provider
from tests.utils import get_localnet

PATH = Path("anchor/tests/chat/")

localnet = get_localnet(PATH)


@fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@fixture(scope="module")
async def program(localnet) -> Program:
    """Create a Program instance."""
    workspace = create_workspace(PATH)
    return workspace["chat"]


@fixture(scope="module")
async def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    return program.provider


@fixture(scope="module")
async def created_chatroom(program: Program) -> Keypair:
    chatroom = Keypair()
    await program.rpc["createChatRoom"](
        "Test Chat",
        ctx=Context(
            accounts={
                "chatRoom": chatroom.public_key,
                "rent": SYSVAR_RENT_PUBKEY,
            },
            instructions=[
                await program.account["ChatRoom"].create_instruction(chatroom),
            ],
            signers=[chatroom],
        ),
    )
    return chatroom


@fixture(scope="module")
async def created_user(
    created_chatroom: Keypair, program: Program
) -> Tuple[PublicKey, PublicKey]:
    authority = program.provider.wallet.public_key
    user, bump = PublicKey.find_program_address([bytes(authority)], program.program_id)
    await program.rpc["createUser"](
        "My User",
        bump,
        ctx=Context(
            accounts={
                "user": user,
                "authority": authority,
                "systemProgram": SYS_PROGRAM_ID,
            }
        ),
    )
    return user, authority


@fixture(scope="module")
async def sent_messages(
    created_user: Tuple[PublicKey, PublicKey],
    created_chatroom: Keypair,
    program: Program,
) -> List[str]:
    user, authority = created_user
    num_messages = 10
    messages = [
        "".join(random.choices(string.ascii_uppercase + string.digits, k=13))
        for i in range(num_messages)
    ]
    for i, msg in enumerate(messages):
        print(f"senging message {i}")
        await program.rpc["sendMessage"](
            msg,
            ctx=Context(
                accounts={
                    "user": user,
                    "authority": authority,
                    "chatRoom": created_chatroom.public_key,
                },
            ),
        )
    return messages


@mark.asyncio
async def test_created_chatroom(created_chatroom: Keypair, program: Program) -> None:
    chat = await program.account["ChatRoom"].fetch(created_chatroom.public_key)
    name = bytes(chat["name"]).rstrip(b"\x00").decode("utf-8")
    assert name == "Test Chat"
    assert len(chat["messages"]) == 33607
    assert chat["head"] == 0
    assert chat["tail"] == 0


@mark.asyncio
async def test_created_user(
    created_user: Tuple[PublicKey, PublicKey],
    program: Program,
) -> None:
    user, authority = created_user
    account = await program.account["User"].fetch(user)
    assert account["name"] == "My User"
    assert account["authority"] == authority


@mark.asyncio
async def test_sent_messages(
    program: Program,
    created_chatroom: Keypair,
    sent_messages: List[str],
    created_user: Tuple[PublicKey, PublicKey],
) -> None:
    user, _ = created_user
    chat = await program.account["ChatRoom"].fetch(created_chatroom.public_key)
    for i, msg in enumerate(chat["messages"]):
        if i < len(sent_messages):
            data = bytes(msg["data"]).rstrip(b"\x00").decode("utf-8")
            print(f"Message {data}")
            assert msg["from"] == user
            assert data == sent_messages[i]
        else:
            assert msg["data"] == [0] * 280  # noqa: WPS435
