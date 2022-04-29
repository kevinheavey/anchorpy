import subprocess

from pytest import fixture

from anchorpy.pytest_plugin import workspace_fixture

workspace = workspace_fixture("anchor/tests/cfo", build_cmd="anchor build --skip-lint")


@fixture(scope="module")
def build_lockup() -> None:
    subprocess.run(  # noqa: S603,S607
        ["anchor", "build"],
        check=True,
        cwd="anchor/tests/lockup",
    )


def boilerplate(build_lockup, workspace):
    """TODO."""
