"""Mimics anchor/tests/misc/tests/misc.js."""
import asyncio
from pathlib import Path, PosixPath
from typing import Dict
from pytest import raises, mark, fixture
from anchorpy import ProgramError, Program, create_workspace, close_workspace, Context
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.transaction import AccountMeta, Transaction, TransactionInstruction
from solana.rpc.core import RPCException
from tests.utils import get_localnet

PATH = Path("anchor/tests/misc/")

localnet = get_localnet(PATH)


@fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@fixture(scope="module")
async def workspace(localnet) -> Dict[str, Program]:
    wspace = create_workspace(PATH)
    yield wspace
    await close_workspace(wspace)


@fixture(scope="module")
async def program(workspace: Dict[str, Program]) -> Program:
    return workspace["misc"]


@fixture(scope="module")
async def misc2program(workspace: Dict[str, Program]) -> Program:
    return workspace["misc2"]


@mark.asyncio
async def test_can_use_u128_and_i128(program: Program) -> None:
    data = Keypair()
    await program.rpc["initialize"](
        1234,
        22,
        ctx=Context(
            accounts={"data": data.public_key, "rent": SYSVAR_RENT_PUBKEY},
            signers=[data],
            instructions=[await program.account["Data"].create_instruction(data)],
        ),
    )
    data_account = await program.account["Data"].fetch(data.public_key)
    assert data_account["udata"] == 1234
    assert data_account["idata"] == 22


@fixture(scope="module")
async def keypair_after_testU16(program: Program) -> Keypair:
    data = Keypair()
    await program.rpc["testU16"](
        99,
        ctx=Context(
            accounts={"myAccount": data.public_key, "rent": SYSVAR_RENT_PUBKEY},
            signers=[data],
            instructions=[await program.account["DataU16"].create_instruction(data)],
        ),
    )
    return data


@mark.asyncio
async def test_can_use_u16(
    program: Program,
    keypair_after_testU16: Keypair,
) -> None:
    data_account = await program.account["DataU16"].fetch(
        keypair_after_testU16.public_key,
    )
    assert data_account["data"] == 99


@mark.asyncio
async def test_can_embed_programs_into_genesis_from_toml(program: Program) -> None:
    pid = PublicKey("FtMNMKp9DZHKWUyVAsj3Q5QV8ow4P3fUPP7ZrWEQJzKr")
    acc_info_raw = await program.provider.client.get_account_info(pid)
    assert acc_info_raw["result"]["value"]["executable"] is True


@mark.asyncio
async def test_can_use_owner_constraint(
    program: Program, keypair_after_testU16: Keypair
) -> None:
    await program.rpc["testOwner"](
        ctx=Context(
            accounts={
                "data": keypair_after_testU16.public_key,
                "misc": program.program_id,
            },
        ),
    )
    with raises(ProgramError):
        await program.rpc["testOwner"](
            ctx=Context(
                accounts={
                    "data": program.provider.wallet.public_key,
                    "misc": program.program_id,
                },
            ),
        )


@mark.asyncio
async def test_can_use_executable_attribute(program: Program) -> None:
    await program.rpc["testExecutable"](
        ctx=Context(accounts={"program": program.program_id}),
    )
    # sleep so we don't get AlreadyProcessed error
    await asyncio.sleep(10)
    with raises(ProgramError):
        await program.rpc["testExecutable"](
            ctx=Context(accounts={"program": program.provider.wallet.public_key}),
        )


@mark.asyncio
async def test_can_retrieve_events_when_simulating_transaction(
    program: Program,
) -> None:
    resp = await program.simulate["testSimulate"](44)
    expected_raw = [
        "Program Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS invoke [1]",
        "Program log: NgyCA9omwbMsAAAA",
        "Program log: fPhuIELK/k7SBAAA",
        "Program log: jvbowsvlmkcJAAAA",
        (
            "Program Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS consumed "
            "4694 of 200000 compute units"
        ),
        "Program Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS success",
    ]
    events = resp.events
    assert resp.raw == expected_raw
    assert events[0]["name"] == "E1"
    assert events[0]["data"]["data"] == 44
    assert events[1]["name"] == "E2"
    assert events[1]["data"]["data"] == 1234
    assert events[2]["name"] == "E3"
    assert events[2]["data"]["data"] == 9


@mark.asyncio
async def test_can_use_i8_in_idl(program: Program) -> None:
    data = Keypair()
    await program.rpc["testI8"](
        -3,
        ctx=Context(
            accounts={"data": data.public_key, "rent": SYSVAR_RENT_PUBKEY},
            instructions=[await program.account["DataI8"].create_instruction(data)],
            signers=[data],
        ),
    )
    data_account = await program.account["DataI8"].fetch(data.public_key)
    assert data_account["data"] == -3


@fixture(scope="module")
async def data_i16_keypair(program: Program) -> Keypair:
    data = Keypair()
    await program.rpc["testI16"](
        -2048,
        ctx=Context(
            accounts={"data": data.public_key, "rent": SYSVAR_RENT_PUBKEY},
            instructions=[await program.account["DataI16"].create_instruction(data)],
            signers=[data],
        ),
    )
    return data


@mark.asyncio
async def test_can_use_i16_in_idl(program: Program, data_i16_keypair: Keypair) -> None:
    data_account = await program.account["DataI16"].fetch(data_i16_keypair.public_key)
    assert data_account["data"] == -2048


@mark.asyncio
async def test_can_use_base58_strings_to_fetch_account(
    program: Program,
    data_i16_keypair: Keypair,
) -> None:
    data_account = await program.account["DataI16"].fetch(
        str(data_i16_keypair.public_key),
    )
    assert data_account["data"] == -2048


@mark.asyncio
# @mark.xfail
async def test_fail_to_close_account_when_sending_lamports_to_itself(
    program: Program, data_i16_keypair: Keypair
) -> None:
    ix = program.instruction["testClose"](
        ctx=Context(
            accounts={
                "data": data_i16_keypair.public_key,
                "solDest": data_i16_keypair.public_key,
            },
        ),
    )
    print(ix)
    print(ix.data.hex())
    with raises(ProgramError) as excinfo:
        await program.rpc["testClose"](
            ctx=Context(
                accounts={
                    "data": data_i16_keypair.public_key,
                    "solDest": data_i16_keypair.public_key,
                },
            ),
        )
    assert excinfo.value.code == 151
    assert excinfo.value.msg == "A close constraint was violated"
