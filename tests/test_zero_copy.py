"""Mimics anchor/tests/zero-copy"""
from pathlib import Path
from typing import AsyncGenerator

from pytest import mark, fixture, raises
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.system_program import SYS_PROGRAM_ID
from solana.rpc.core import RPCException

from anchorpy import (
    Program,
    create_workspace,
    close_workspace,
    Context,
    Provider,
    get_localnet,
)

PATH = Path("anchor/tests/zero-copy")
DEFAULT_PUBKEY = PublicKey("11111111111111111111111111111111")

localnet = get_localnet(PATH)


@fixture(scope="module")
async def workspace(localnet) -> AsyncGenerator[dict[str, Program], None]:
    wspace = create_workspace(PATH)
    yield wspace
    await close_workspace(wspace)


@fixture(scope="module")
async def program(workspace: dict[str, Program]) -> Program:
    return workspace["zero_copy"]


@fixture(scope="module")
async def program_cpi(workspace: dict[str, Program]) -> Program:
    return workspace["zero_cpi"]


@fixture(scope="module")
async def provider(program: Program) -> Provider:
    """Get a Provider instance."""
    return program.provider


@fixture(scope="module")
async def foo(program: Program) -> Keypair:
    foo_keypair = Keypair()
    await program.rpc["createFoo"](
        ctx=Context(
            accounts={
                "foo": foo_keypair.public_key,
                "authority": program.provider.wallet.public_key,
                "rent": SYSVAR_RENT_PUBKEY,
            },
            instructions=[await program.account["Foo"].create_instruction(foo_keypair)],
            signers=[foo_keypair],
        )
    )
    return foo_keypair


@mark.asyncio
async def test_create_foo(foo: Keypair, provider: Provider, program: Program) -> None:
    account = await program.account["Foo"].fetch(foo.public_key)
    assert account.authority == provider.wallet.public_key
    assert account.data == 0
    assert account.secondData == 0
    assert account.secondAuthority == list(bytes(provider.wallet.public_key))


@fixture(scope="module")
async def update_foo(program: Program, foo: Keypair) -> None:
    await program.rpc["updateFoo"](
        1234,
        ctx=Context(
            accounts={
                "foo": foo.public_key,
                "authority": program.provider.wallet.public_key,
            },
        ),
    )


@mark.asyncio
async def test_update_foo(
    foo: Keypair, provider: Provider, program: Program, update_foo: None
) -> None:
    account = await program.account["Foo"].fetch(foo.public_key)
    assert account.authority == provider.wallet.public_key
    assert account.data == 1234
    assert account.secondData == 0
    assert account.secondAuthority == list(bytes(program.provider.wallet.public_key))


@fixture(scope="module")
async def update_foo_second(program: Program, foo: Keypair, update_foo: None) -> None:
    await program.rpc["updateFooSecond"](
        55,
        ctx=Context(
            accounts={
                "foo": foo.public_key,
                "secondAuthority": program.provider.wallet.public_key,
            },
        ),
    )


@mark.asyncio
async def test_update_foo_second(
    foo: Keypair, provider: Provider, program: Program, update_foo_second: None
) -> None:
    account = await program.account["Foo"].fetch(foo.public_key)
    assert account.authority == provider.wallet.public_key
    assert account.data == 1234
    assert account.secondData == 55
    assert account.secondAuthority == list(bytes(program.provider.wallet.public_key))


@fixture(scope="module")
async def bar(
    program: Program, provider: Provider, foo: Keypair, update_foo_second: None
) -> PublicKey:
    bar_pubkey = PublicKey.find_program_address(
        [bytes(provider.wallet.public_key), bytes(foo.public_key)], program.program_id
    )[0]
    await program.rpc["createBar"](
        ctx=Context(
            accounts={
                "bar": bar_pubkey,
                "authority": provider.wallet.public_key,
                "foo": foo.public_key,
                "systemProgram": SYS_PROGRAM_ID,
            }
        )
    )
    return bar_pubkey


@mark.asyncio
async def test_create_bar(provider: Provider, program: Program, bar: PublicKey) -> None:
    account = await program.account["Bar"].fetch(bar)
    assert account.authority == provider.wallet.public_key
    assert account.data == 0


@fixture(scope="module")
async def update_associated_zero_copy_account(
    program: Program,
    provider: Provider,
    foo: Keypair,
    bar: PublicKey,
) -> None:
    await program.rpc["updateBar"](
        99,
        ctx=Context(
            accounts={
                "bar": bar,
                "authority": program.provider.wallet.public_key,
                "foo": foo.public_key,
            },
        ),
    )


@mark.asyncio
async def test_update_associated_zero_copy_account(
    provider: Provider,
    program: Program,
    bar: PublicKey,
    update_associated_zero_copy_account: None,
) -> None:
    account = await program.account["Bar"].fetch(bar)
    assert account.authority == provider.wallet.public_key
    assert account.data == 99


@fixture(scope="module")
async def check_cpi(
    program_cpi: Program,
    program: Program,
    provider: Provider,
    foo: Keypair,
    bar: PublicKey,
    update_associated_zero_copy_account: None,
) -> None:
    await program_cpi.rpc["checkCpi"](
        1337,
        ctx=Context(
            accounts={
                "bar": bar,
                "authority": provider.wallet.public_key,
                "foo": foo.public_key,
                "zeroCopyProgram": program.program_id,
            },
        ),
    )


@mark.asyncio
async def test_check_cpi(
    provider: Provider,
    program: Program,
    bar: PublicKey,
    check_cpi: None,
) -> None:
    account = await program.account["Bar"].fetch(bar)
    assert account.authority == provider.wallet.public_key
    assert account.data == 1337


@fixture(scope="module")
async def event_q(
    program: Program,
    check_cpi: None,
) -> Keypair:
    event_q_keypair = Keypair()
    size = 1000000 + 8
    await program.rpc["createLargeAccount"](
        ctx=Context(
            accounts={
                "eventQ": event_q_keypair.public_key,
                "rent": SYSVAR_RENT_PUBKEY,
            },
            instructions=[
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
    account = await program.account["EventQ"].fetch(event_q.public_key)
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
    await program.rpc["updateLargeAccount"](
        0,
        48,
        ctx=Context(
            accounts={
                "eventQ": event_q.public_key,
                "from": provider.wallet.public_key,
            },
        ),
    )
    account = await program.account["EventQ"].fetch(event_q.public_key)
    events = account.events
    assert len(events) == 25000
    for idx, event in enumerate(events):
        if idx == 0:
            assert event.from_ == provider.wallet.public_key
            assert event.data == 48
        else:
            assert event.from_ == DEFAULT_PUBKEY
            assert event.data == 0
    await program.rpc["updateLargeAccount"](
        11111,
        1234,
        ctx=Context(
            accounts={
                "eventQ": event_q.public_key,
                "from": provider.wallet.public_key,
            },
        ),
    )
    account = await program.account["EventQ"].fetch(event_q.public_key)
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
    await program.rpc["updateLargeAccount"](
        24999,
        99,
        ctx=Context(
            accounts={
                "eventQ": event_q.public_key,
                "from": provider.wallet.public_key,
            },
        ),
    )
    account = await program.account["EventQ"].fetch(event_q.public_key)
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
        await program.rpc["updateLargeAccount"](
            25000,
            99,
            ctx=Context(
                accounts={
                    "eventQ": event_q.public_key,
                    "from": provider.wallet.public_key,
                },
            ),
        )
