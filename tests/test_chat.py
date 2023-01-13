import random
import string

from anchorpy import Context, Program, Provider
from anchorpy.pytest_plugin import workspace_fixture
from pytest import fixture, mark
from pytest_asyncio import fixture as async_fixture
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT

workspace = workspace_fixture(
    "anchor/tests/chat/", build_cmd="anchor build --skip-lint"
)


@fixture(scope="module")
def program(workspace) -> Program:
    """Create a Program instance."""
    return workspace["chat"]


@fixture(scope="module")
async def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    return program.provider


@async_fixture(scope="module")
async def created_chatroom(program: Program) -> Keypair:
    chatroom = Keypair()
    await program.rpc["create_chat_room"](
        "Test Chat",
        ctx=Context(
            accounts={
                "chat_room": chatroom.pubkey(),
                "rent": RENT,
            },
            pre_instructions=[
                await program.account["ChatRoom"].create_instruction(chatroom),
            ],
            signers=[chatroom],
        ),
    )
    return chatroom


@async_fixture(scope="module")
async def created_user(
    created_chatroom: Keypair, program: Program
) -> tuple[Pubkey, Pubkey]:
    authority = program.provider.wallet.public_key
    user, bump = Pubkey.find_program_address([bytes(authority)], program.program_id)
    await program.rpc["create_user"](
        "My User",
        ctx=Context(
            accounts={
                "user": user,
                "authority": authority,
                "system_program": SYS_PROGRAM_ID,
            }
        ),
    )
    return user, authority


@async_fixture(scope="module")
async def sent_messages(
    created_user: tuple[Pubkey, Pubkey],
    created_chatroom: Keypair,
    program: Program,
) -> list[str]:
    user, authority = created_user
    num_messages = 10
    to_choose = string.ascii_uppercase + string.digits
    messages = ["".join(random.choices(to_choose, k=13)) for _ in range(num_messages)]
    for i, msg in enumerate(messages):
        print(f"sending message {i}")
        await program.rpc["send_message"](
            msg,
            ctx=Context(
                accounts={
                    "user": user,
                    "authority": authority,
                    "chat_room": created_chatroom.pubkey(),
                },
            ),
        )
    return messages


@mark.asyncio
async def test_created_chatroom(created_chatroom: Keypair, program: Program) -> None:
    chat = await program.account["ChatRoom"].fetch(created_chatroom.pubkey())
    name = bytes(chat.name).rstrip(b"\x00").decode("utf-8")
    assert name == "Test Chat"
    assert len(chat.messages) == 33607
    assert chat.head == 0
    assert chat.tail == 0


@mark.asyncio
async def test_created_user(
    created_user: tuple[Pubkey, Pubkey],
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
    sent_messages: list[str],
    created_user: tuple[Pubkey, Pubkey],
) -> None:
    user, _ = created_user
    chat = await program.account["ChatRoom"].fetch(created_chatroom.pubkey())
    for i, msg in enumerate(chat.messages):
        if i < len(sent_messages):
            data = bytes(msg.data).rstrip(b"\x00").decode("utf-8")
            print(f"Message {data}")
            assert msg.from_ == user
            assert data == sent_messages[i]
        else:
            assert msg.data == [0] * 280
