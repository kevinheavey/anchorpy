"""Pytest config."""
import asyncio
import subprocess
from pathlib import Path

from pytest import fixture

# Since our other fixtures have module scope, we need to define
# this event_loop fixture and give it module scope otherwise
# pytest-asyncio will break.


@fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@fixture(scope="session")
def project_parent_dir(tmpdir_factory) -> Path:
    return Path(tmpdir_factory.mktemp("temp"))


@fixture(scope="session")
def project_dir(project_parent_dir: Path) -> Path:
    proj_dir = project_parent_dir / "tmp"
    command = (
        f"anchorpy client-gen tests/idls/clientgen_example_program.json {proj_dir} "
        "--program-id 3rTQ3R4B2PxZrAyx7EUefySPgZY8RhJf16cZajbmrzp8 --pdas"
    )
    subprocess.run(
        command,
        shell=True,
        check=True,
    )
    return proj_dir
