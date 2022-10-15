"""Mimics anchor/tests/misc/tests/misc.js."""
from dataclasses import dataclass
from pytest import mark, fixture
from construct import Int32sl, Int64ul
from anchorpy import Program, Context
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.system_program import (
    create_account,
    CreateAccountParams,
)
from anchorpy.pytest_plugin import workspace_fixture
from anchorpy.workspace import WorkspaceType


workspace = workspace_fixture(
    "anchor/tests/pyth/", build_cmd="anchor build --skip-lint"
)


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    return workspace["pyth"]


async def create_price_feed(
    oracle_program: Program,
    init_price: int,
    expo: int,
) -> PublicKey:
    conf = int((init_price / 10) * 10**-expo)
    space = 3312
    mbre_resp = (
        await oracle_program.provider.connection.get_minimum_balance_for_rent_exemption(
            space,
        )
    )
    collateral_token_feed = Keypair()
    await oracle_program.rpc["initialize"](
        int(init_price * 10**-expo),
        expo,
        conf,
        ctx=Context(
            accounts={"price": collateral_token_feed.public_key},
            signers=[collateral_token_feed],
            pre_instructions=[
                create_account(
                    CreateAccountParams(
                        from_pubkey=oracle_program.provider.wallet.public_key,
                        new_account_pubkey=collateral_token_feed.public_key,
                        space=3312,
                        lamports=mbre_resp.value,
                        program_id=oracle_program.program_id,
                    ),
                ),
            ],
        ),
    )
    return collateral_token_feed.public_key


async def set_feed_price(
    oracle_program: Program,
    new_price: int,
    price_feed: PublicKey,
) -> None:
    data = await get_feed_data(oracle_program, price_feed)
    await oracle_program.rpc["set_price"](
        int(new_price * 10**-data.exponent),
        ctx=Context(accounts={"price": price_feed}),
    )


@dataclass
class PriceData:
    exponent: int
    price: int


def parse_price_data(data: bytes) -> PriceData:
    exponent = Int32sl.parse(data[20:24])
    raw_price = Int64ul.parse(data[208:216])
    price = raw_price * 10**exponent
    return PriceData(exponent, price)


async def get_feed_data(
    oracle_program: Program,
    price_feed: PublicKey,
) -> PriceData:
    info = await oracle_program.provider.connection.get_account_info(
        price_feed,
        encoding="base64",
    )
    val = info.value
    if val is None:
        raise ValueError("Account does not exist.")
    return parse_price_data(val.data)


@mark.asyncio
async def test_initialize(program: Program) -> None:
    price = 50000
    price_feed_address = await create_price_feed(
        oracle_program=program,
        init_price=price,
        expo=-6,
    )
    feed_data = await get_feed_data(program, price_feed_address)
    assert feed_data.price == price


@mark.asyncio
async def test_change_feed_price(program: Program) -> None:
    price = 50000
    expo = -7
    price_feed_address = await create_price_feed(
        oracle_program=program,
        init_price=price,
        expo=expo,
    )
    feed_data_before = await get_feed_data(program, price_feed_address)
    assert feed_data_before.price == price
    assert feed_data_before.exponent == expo
    new_price = 55000
    await set_feed_price(program, new_price, price_feed_address)
    feed_data_after = await get_feed_data(program, price_feed_address)
    assert feed_data_after.price == new_price
    assert feed_data_after.exponent == expo


@mark.asyncio
async def test_enum(program: Program) -> None:
    corp_act = program.type["CorpAction"]
    assert corp_act.NoCorpAct().index == 0
