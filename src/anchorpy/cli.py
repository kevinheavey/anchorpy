import os
from pathlib import Path
from contextlib import contextmanager
import typer
from IPython import embed
from anchorpy import create_workspace
from anchorpy.template import INIT_TESTS

app = typer.Typer()


@contextmanager
def _set_directory(path: Path):
    """Sets the cwd within the context

    Args:
        path (Path): The path to the cwd

    Yields:
        None
    """

    origin = Path().absolute()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)


def _search_upwards_for_project_root() -> Path:
    """Search in the current directory and all directories above it
    for an Anchor.toml file.

    Args:
        filename: The filename to look for.

    Returns:
        The location of the first Anchor.toml file found
    """
    search_dir = Path.cwd()
    root = Path(search_dir.root)

    while search_dir != root:
        attempt = search_dir / "Anchor.toml"
        if attempt.exists():
            return search_dir
        search_dir = search_dir.parent

    raise FileNotFoundError("Not in Anchor workspace.")


@app.callback()
def callback():
    """AnchorPy CLI."""  # noqa: D403


@app.command()
def shell():
    """Start IPython shell with AnchorPy workspace object initialized.

    Note that you should run `anchor localnet` before `anchorpy shell`.
    """
    path = _search_upwards_for_project_root()
    workspace = create_workspace(path)  # noqa: F841
    embed(
        colors="neutral",
        using="asyncio",
        banner2="Hint: type `workspace` to see the Anchor workspace object.\n",
    )


@app.command()
def init(
    program_name: str = typer.Argument(..., help="The name of the Anchor program.")
):
    """Create a basic Python test file for an Anchor program.

    This does not replace `anchor init`, but rather should be
    run after it.

    The test file will live at `tests/test_$PROGRAM_NAME.py`.
    """
    file_contents = INIT_TESTS.format(program_name)
    project_root = _search_upwards_for_project_root()
    file_path = project_root / "tests" / f"test_{program_name}.py"
    if file_path.exists():
        raise FileExistsError(file_path)
    file_path.write_text(file_contents)


if __name__ == "__main__":
    app()
