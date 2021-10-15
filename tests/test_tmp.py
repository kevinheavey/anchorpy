import pytest
import asyncio


@pytest.fixture
async def my_num():
    await asyncio.sleep(0.1)
    yield 3


@pytest.mark.asyncio
async def test_something(my_num):
    await asyncio.sleep(0.5)
    print("asserting!")
    assert my_num == 3
