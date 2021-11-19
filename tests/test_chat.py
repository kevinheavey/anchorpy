from pathlib import Path
from typing import AsyncGenerator, List, Tuple
import random
import string

from pytest import mark, fixture
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.system_program import SYS_PROGRAM_ID

from anchorpy import Program, create_workspace, close_workspace, Context, Provider
from anchorpy.pytest_plugin import localnet_fixture

PATH = Path("anchor/tests/chat/")

localnet = localnet_fixture(PATH)


@fixture(scope="module")
async def program(localnet) -> AsyncGenerator[Program, None]:
    """Create a Program instance."""
    workspace = create_workspace(PATH)
    yield workspace["chat"]
    await close_workspace(workspace)


@fixture(scope="module")
async def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    return program.provider


@fixture(scope="module")
async def created_chatroom(program: Program) -> Keypair:
    chatroom = Keypair()
    await program.rpc["create_chat_room"](
        "Test Chat",
        ctx=Context(
            accounts={
                "chat_room": chatroom.public_key,
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
    await program.rpc["create_user"](
        "My User",
        bump,
        ctx=Context(
            accounts={
                "user": user,
                "authority": authority,
                "system_program": SYS_PROGRAM_ID,
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
    to_choose = string.ascii_uppercase + string.digits
    messages = [
        "".join(random.choices(to_choose, k=13))  # noqa: S311
        for _ in range(num_messages)
    ]
    for i, msg in enumerate(messages):
        print(f"sending message {i}")
        await program.rpc["send_message"](
            msg,
            ctx=Context(
                accounts={
                    "user": user,
                    "authority": authority,
                    "chat_room": created_chatroom.public_key,
                },
            ),
        )
    return messages


@mark.asyncio
async def test_created_chatroom(created_chatroom: Keypair, program: Program) -> None:
    chat = await program.account["ChatRoom"].fetch(created_chatroom.public_key)
    name = bytes(chat.name).rstrip(b"\x00").decode("utf-8")
    assert name == "Test Chat"
    assert len(chat.messages) == 33607
    assert chat.head == 0
    assert chat.tail == 0


@mark.asyncio
async def test_created_user(
    created_user: Tuple[PublicKey, PublicKey],
    program: Program,
) -> None:
    user, authority = created_user
    account = await program.account["User"].fetch(user)
    assert account.name == "My User"
    assert account.authority == authority


@mark.asyncio
async def test_sent_messages(
    program: Program,
    created_chatroom: Keypair,
    sent_messages: List[str],
    created_user: Tuple[PublicKey, PublicKey],
) -> None:
    user, _ = created_user
    chat = await program.account["ChatRoom"].fetch(created_chatroom.public_key)
    for i, msg in enumerate(chat.messages):
        if i < len(sent_messages):
            data = bytes(msg.data).rstrip(b"\x00").decode("utf-8")
            print(f"Message {data}")
            assert msg.from_ == user
            assert data == sent_messages[i]
        else:
            assert msg.data == [0] * 280  # noqa: WPS435
