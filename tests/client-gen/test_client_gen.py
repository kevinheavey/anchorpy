from pathlib import Path
from filecmp import dircmp
import subprocess
from pytest import fixture
from anchorpy.pytest_plugin import localnet_fixture
from anchorpy import Provider

EXAMPLE_PROGRAM_DIR = Path("ts-reference/tests/example-program")

localnet = localnet_fixture(EXAMPLE_PROGRAM_DIR)

@fixture(scope="session")
async def provider() -> Provider:
    prov = Provider.local()
    yield prov
    await prov.close()

@fixture(scope="session")
def project_parent_dir(tmpdir_factory) -> Path:
    return Path(tmpdir_factory.mktemp("temp"))


@fixture(scope="session")
def project_dir(project_parent_dir: Path) -> Path:
    proj_dir = project_parent_dir / "tmp"
    subprocess.run(f"anchorpy client-gen ts-reference/tests/example-program-gen/idl.json {proj_dir} --program-id 3rTQ3R4B2PxZrAyx7EUefySPgZY8RhJf16cZajbmrzp8", shell=True, check=True)
    return proj_dir

def has_differences(dcmp: dircmp) -> bool:
    differences = dcmp.left_only + dcmp.right_only + dcmp.diff_files
    if differences:
        return True
    return any([has_differences(subdcmp) for subdcmp in dcmp.subdirs.values()])

def test_generated_as_expected(project_dir: Path) -> None:
    dcmp = dircmp(project_dir, "tests/client-gen/example_program_gen")
    assert not has_differences(dcmp)