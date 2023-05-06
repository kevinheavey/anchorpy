# Testing with AnchorPy

## Approaches

There are two ways to test Anchor programs using AnchorPy:

1. Using the AnchorPy Pytest plugin.
2. Using `anchor test` and modifying `Anchor.toml`.

## 1. Pytest plugin

AnchorPy provides a `workspace_fixture` function that creates a Pytest fixture.
This fixture runs `anchor localnet` in the project root and shuts down the localnet
when the tests are done.

With this approach you're just running regular Pytest tests.
This lets you do some things that you can't do with `anchor test`,
like integrating closely with your IDE or opening a debugger when a test fails (`pytest --pdb`).

Here's how it looks with the `basic-1` tests:

```python
from pytest import fixture, mark
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID

from anchorpy import Context, Program, workspace_fixture, WorkspaceType

workspace = workspace_fixture("anchor/examples/tutorial/basic-1")

# Since our other fixtures have module scope, we need to define
# this event_loop fixture and give it module scope otherwise
# pytest-asyncio will break.

@fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@fixture(scope="module")
def program(workspace: WorkspaceType) -> Program:
    """Create a Program instance."""
    return workspace["basic_1"]


@fixture(scope="module")
async def initialized_account(program: Program) -> Keypair:
    """Generate a keypair and initialize it."""
    my_account = Keypair()
    await program.rpc["initialize"](
        1234,
        ctx=Context(
            accounts={
                "my_account": my_account.pubkey(),
                "user": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[my_account],
        ),
    )
    return my_account


@mark.asyncio
async def test_create_and_initialize_account(
    program: Program,
    initialized_account: Keypair,
) -> None:
    """Test creating and initializing account in single tx."""
    account = await program.account["MyAccount"].fetch(initialized_account.pubkey())
    assert account.data == 1234


@mark.asyncio
async def test_update_previously_created_account(
    initialized_account: Keypair,
    program: Program,
) -> None:
    """Test updating a previously created account."""
    await program.rpc["update"](
        4321,
        ctx=Context(accounts={"my_account": initialized_account.pubkey()}),
    )
    account = await program.account["MyAccount"].fetch(initialized_account.pubkey())
    assert account.data == 4321

```

You can just run these tests with `pytest` (or have your IDE run them).
!!! note
    There is also a lower-level `localnet_fixture` function that sets up a localnet for a
    particular project but doesn't return a workspace.

## 2. Anchor test


Anchor lets you run whatever tests you want using the `[scripts]` section of `Anchor.toml`.
This means we can call Pytest inside the `anchor test` workflow. This is more limited
than the Pytest plugin but is more like the standard Anchor way of doing things.

Here's how the `basic-1` tests look using `anchor test` and Pytest (but not the ):

```python
# test_basic_1.py
import asyncio
from pathlib import Path
from pytest import fixture, mark
from anchorpy import create_workspace, close_workspace, Context, Program
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID


# Since our other fixtures have module scope, we need to define
# this event_loop fixture and give it module scope otherwise
# pytest-asyncio will break.

@fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@fixture(scope="module")
async def program() -> Program:
    workspace = create_workspace()
    yield workspace["basic_1"]
    await close_workspace(workspace)


@fixture(scope="module")
async def initialized_account(program: Program) -> Keypair:
    my_account = Keypair()
    await program.rpc["initialize"](
        1234,
        ctx=Context(
            accounts={
                "my_account": my_account.pubkey(),
                "user": program.provider.wallet.public_key,
                "system_program": SYS_PROGRAM_ID,
            },
            signers=[my_account],
        ),
    )
    return my_account


@mark.asyncio
async def test_create_and_initialize_account(
    program: Program, initialized_account: Keypair
) -> None:
    """Test creating and initializing account in single tx."""
    account = await program.account["MyAccount"].fetch(initialized_account.pubkey())
    assert account.data == 1234


@mark.asyncio
async def test_update_previously_created_account(
    initialized_account: Keypair, program: Program
) -> None:
    """Test updating a previously created account."""
    await program.rpc["update"](
        4321, ctx=Context(accounts={"myAccount": initialized_account.pubkey()})
    )
    account = await program.account["MyAccount"].fetch(initialized_account.pubkey())
    assert account.data == 4321

```

Just paste this code into a file called `test_basic_1.py`
in `anchor/examples/tutorial/basic-1/tests/`, and change the `scripts` section of `Anchor.toml`
to look like this:

```toml
[scripts]
test = "pytest"

```

Then run `anchor test` and voila!.

!!! note
    You must have `pytest-asyncio` installed for `test_basic_1.py` to work.

## Bankrun Integration

AnchorPy comes with a `bankrun_fixture` to help use
[`solders.bankrun`](https://kevinheavey.github.io/solders/examples/bankrun.html) in tests.

If you haven't heard, `bankrun` is a much faster and more convenient alternative to
`solana-test-validator`. Long test suites are about 40 times faster with `bankrun`,
and for short test suites the difference is even bigger because `bankrun` has neglible
startup time.

`bankrun_fixture` calls `bankrun.start()` and deploys all the programs in the current
Anchor workspace to the test envioronment.
Check out [this example](https://github.com/kevinheavey/anchorpy/blob/main/tests/test_basic_3_bankrun.py).

