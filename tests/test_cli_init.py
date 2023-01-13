import subprocess
from pathlib import Path

from pytest import fixture

PATH = Path("anchor/examples/tutorial/basic-0")
PROJECT_NAME = "foo"


@fixture(scope="session")
def project_parent_dir(tmpdir_factory) -> Path:
    return Path(tmpdir_factory.mktemp("temp"))


@fixture(scope="session")
def project_dir(project_parent_dir: Path) -> Path:
    subprocess.run(["anchor", "init", PROJECT_NAME], cwd=project_parent_dir, check=True)
    proj_dir = project_parent_dir / PROJECT_NAME
    subprocess.run(["anchor", "build"], cwd=proj_dir, check=True)
    subprocess.run(["anchorpy", "init", PROJECT_NAME], cwd=proj_dir, check=True)
    return proj_dir


def test_init(project_dir: Path):
    subprocess.run("pytest", cwd=project_dir, check=True)
