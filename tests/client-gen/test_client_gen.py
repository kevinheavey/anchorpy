from pathlib import Path
import filecmp
import subprocess
from pytest import fixture
from anchorpy.pytest_plugin import localnet_fixture

EXAMPLE_PROGRAM_DIR = Path("ts-reference/tests/example-program")

localnet = localnet_fixture(EXAMPLE_PROGRAM_DIR)
