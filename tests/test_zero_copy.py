"""Mimics anchor/tests/zero-copy."""
from pathlib import Path

from anchorpy import (
    Context,
    Program,
    Provider,
)
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType
from pytest import fixture, mark, raises
from pytest_asyncio import fixture as async_fixture
from solana.rpc.core import RPCException
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT

PATH = Path("anchor/tests/zero-copy")
DEFAULT_PUBKEY = Pubkey.from_string("11111111111111111111111111111111")

workspace = workspace_fixture(
    "anchor/tests/zero-copy", build_cmd="anchor build --skip-lint"
)


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    return workspace["zero_copy"]


@fixture(scope="module")
def program_cpi(workspace: dict[str, Program]) -> Program:
    return workspace["zero_cpi"]


@async_fixture(scope="module")
async def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    print(program.idl)
    return program.provider


@async_fixture(scope="module")
async def foo(program: Program) -> Keypair:
    foo_keypair = Keypair()
    await program.rpc["create_foo"](
        ctx=Context(
            accounts={
                "foo": foo_keypair.pubkey(),
                "authority": program.provider.wallet.public_key,
                "rent": RENT,
            },
            pre_instructions=[
                await program.account["Foo"].create_instruction(foo_keypair)
            ],
            signers=[foo_keypair],
        )
    )
    return foo_keypair


@mark.asyncio
async def test_create_foo(foo: Keypair, provider: Provider, program: Program) -> None:
    account = await program.account["Foo"].fetch(foo.pubkey())
    assert account.authority == provider.wallet.public_key
    assert account.data == 0
    assert account.second_data == 0
    assert account.second_authority == list(bytes(provider.wallet.public_key))


@async_fixture(scope="module")
async def update_foo(program: Program, foo: Keypair) -> None:
    await program.rpc["update_foo"](
        1234,
        ctx=Context(
            accounts={
                "foo": foo.pubkey(),
                "authority": program.provider.wallet.public_key,
            },
        ),
    )


@mark.asyncio
async def test_update_foo(
    foo: Keypair, provider: Provider, program: Program, update_foo: None
) -> None:
    account = await program.account["Foo"].fetch(foo.pubkey())
    assert account.authority == provider.wallet.public_key
    assert account.data == 1234
    assert account.second_data == 0
    assert account.second_authority == list(bytes(program.provider.wallet.public_key))


@async_fixture(scope="module")
async def update_foo_second(program: Program, foo: Keypair, update_foo: None) -> None:
    await program.rpc["update_foo_second"](
        55,
        ctx=Context(
            accounts={
                "foo": foo.pubkey(),
                "second_authority": program.provider.wallet.public_key,
            },
        ),
    )


@mark.asyncio
async def test_update_foo_second(
    foo: Keypair, provider: Provider, program: Program, update_foo_second: None
) -> None:
    account = await program.account["Foo"].fetch(foo.pubkey())
    assert account.authority == provider.wallet.public_key
    assert account.data == 1234
    assert account.second_data == 55
    assert account.second_authority == list(bytes(program.provider.wallet.public_key))


@async_fixture(scope="module")
async def bar(
    program: Program, provider: Provider, foo: Keypair, update_foo_second: None
) -> Pubkey:
    bar_pubkey = Pubkey.find_program_address(
        [bytes(provider.wallet.public_key), bytes(foo.pubkey())], program.program_id
    )[0]
    await program.rpc["create_bar"](
        ctx=Context(
            accounts={
                "bar": bar_pubkey,
                "authority": provider.wallet.public_key,
                "foo": foo.pubkey(),
                "system_program": SYS_PROGRAM_ID,
            }
        )
    )
    return bar_pubkey


@mark.asyncio
async def test_create_bar(provider: Provider, program: Program, bar: Pubkey) -> None:
    account = await program.account["Bar"].fetch(bar)
    assert account.authority == provider.wallet.public_key
    assert account.data == 0


@async_fixture(scope="module")
async def update_associated_zero_copy_account(
    program: Program,
    provider: Provider,
    foo: Keypair,
    bar: Pubkey,
) -> None:
    await program.rpc["update_bar"](
        99,
        ctx=Context(
            accounts={
                "bar": bar,
                "authority": program.provider.wallet.public_key,
                "foo": foo.pubkey(),
            },
        ),
    )


@mark.asyncio
async def test_update_associated_zero_copy_account(
    provider: Provider,
    program: Program,
    bar: Pubkey,
    update_associated_zero_copy_account: None,
) -> None:
    account = await program.account["Bar"].fetch(bar)
    assert account.authority == provider.wallet.public_key
    assert account.data == 99


@async_fixture(scope="module")
async def check_cpi(
    program_cpi: Program,
    program: Program,
    provider: Provider,
    foo: Keypair,
    bar: Pubkey,
    update_associated_zero_copy_account: None,
) -> None:
    await program_cpi.rpc["check_cpi"](
        1337,
        ctx=Context(
            accounts={
                "bar": bar,
                "authority": provider.wallet.public_key,
                "foo": foo.pubkey(),
                "zero_copy_program": program.program_id,
            },
        ),
    )


@mark.asyncio
async def test_check_cpi(
    provider: Provider,
    program: Program,
    bar: Pubkey,
    check_cpi: None,
) -> None:
    account = await program.account["Bar"].fetch(bar)
    assert account.authority == provider.wallet.public_key
    assert account.data == 1337


@async_fixture(scope="module")
async def event_q(
    program: Program,
    check_cpi: None,
) -> Keypair:
    event_q_keypair = Keypair()
    size = 1000000 + 8
    await program.rpc["create_large_account"](
        ctx=Context(
            accounts={
                "event_q": event_q_keypair.pubkey(),
                "rent": RENT,
            },
            pre_instructions=[
                await program.account["EventQ"].create_instruction(
                    event_q_keypair, size
                )
            ],
            signers=[event_q_keypair],
        ),
    )
    return event_q_keypair


@mark.asyncio
async def test_event_q(
    program: Program,
    event_q: Keypair,
) -> None:
    account = await program.account["EventQ"].fetch(event_q.pubkey())
    events = account.events
    assert len(events) == 25000
    for event in events:
        assert event.from_ == DEFAULT_PUBKEY
        assert event.data == 0


@mark.asyncio
async def test_update_event_q(
    program: Program,
    provider: Provider,
    event_q: Keypair,
) -> None:
    await program.rpc["update_large_account"](
        0,
        48,
        ctx=Context(
            accounts={
                "event_q": event_q.pubkey(),
                "from": provider.wallet.public_key,
            },
        ),
    )
    account = await program.account["EventQ"].fetch(event_q.pubkey())
    events = account.events
    assert len(events) == 25000
    for idx, event in enumerate(events):
        if idx == 0:
            assert event.from_ == provider.wallet.public_key
            assert event.data == 48
        else:
            assert event.from_ == DEFAULT_PUBKEY
            assert event.data == 0
    await program.rpc["update_large_account"](
        11111,
        1234,
        ctx=Context(
            accounts={
                "event_q": event_q.pubkey(),
                "from": provider.wallet.public_key,
            },
        ),
    )
    account = await program.account["EventQ"].fetch(event_q.pubkey())
    events = account.events
    assert len(events) == 25000
    for idx, event in enumerate(events):
        if idx == 0:
            assert event.from_ == provider.wallet.public_key
            assert event.data == 48
        elif idx == 11111:
            assert event.from_ == provider.wallet.public_key
            assert event.data == 1234
        else:
            assert event.from_ == DEFAULT_PUBKEY
            assert event.data == 0
    await program.rpc["update_large_account"](
        24999,
        99,
        ctx=Context(
            accounts={
                "event_q": event_q.pubkey(),
                "from": provider.wallet.public_key,
            },
        ),
    )
    account = await program.account["EventQ"].fetch(event_q.pubkey())
    events = account.events
    assert len(events) == 25000
    for idx, event in enumerate(events):
        if idx == 0:
            assert event.from_ == provider.wallet.public_key
            assert event.data == 48
        elif idx == 11111:
            assert event.from_ == provider.wallet.public_key
            assert event.data == 1234
        elif idx == 24999:
            assert event.from_ == provider.wallet.public_key
            assert event.data == 99
        else:
            assert event.from_ == DEFAULT_PUBKEY
            assert event.data == 0
    with raises(RPCException):
        await program.rpc["update_large_account"](
            25000,
            99,
            ctx=Context(
                accounts={
                    "event_q": event_q.pubkey(),
                    "from": provider.wallet.public_key,
                },
            ),
        )
