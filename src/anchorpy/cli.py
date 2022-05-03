# noqa: D100
import os
from typing import Optional
import json
from pathlib import Path
from contextlib import contextmanager
import typer
from IPython import embed
from anchorpy import create_workspace
from anchorpy.idl import Idl
from anchorpy.template import INIT_TESTS
from anchorpy.clientgen.program_id import gen_program_id
from anchorpy.clientgen.errors import gen_errors
from anchorpy.clientgen.types import gen_types
from anchorpy.clientgen.accounts import gen_accounts
from anchorpy.clientgen.instructions import gen_instructions

app = typer.Typer()


@contextmanager
def _set_directory(path: Path):
    """Set the cwd within the context.

    Args:
        path (Path): The path to the cwd

    Yields:
        None
    """  # noqa: D202

    origin = Path().absolute()
    try:  # noqa: WPS229
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)


def _search_upwards_for_project_root() -> Path:
    """Search in the current directory and all directories above it for an Anchor.toml file.

    Returns:
        The location of the first Anchor.toml file found
    """  # noqa: D205,DAR401
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
    program_name: str = typer.Argument(
        ..., help="The name of the Anchor program."
    )  # noqa: DAR101,DAR401
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


@app.command()
def client_gen(
    idl: Path = typer.Argument(..., help="Anchor IDL file path"),
    out: Path = typer.Argument(..., help="Output directory."),
    program_id: Optional[str] = typer.Option(
        None, help="Optional program ID to be included in the code"
    ),
):
    """Generate Python client code from the specified anchor IDL."""
    with idl.open("r") as f:
        idl_dict = json.load(f)
    idl_obj = Idl.from_json(idl_dict)
    if program_id is None:
        idl_metadata = idl_obj.metadata
        if idl_metadata is None:
            address_from_idl = None
        else:
            address_from_idl = idl_metadata.address
        if address_from_idl is None:
            typer.echo(
                "No program ID found in IDL. Use the --program-id "
                "option to set it manually."
            )
            raise typer.Exit(code=1)
        else:
            program_id_to_use = address_from_idl
    else:
        program_id_to_use = program_id

    typer.echo("generating package...")
    out.mkdir(exist_ok=True)
    (out / "__init__.py").touch()
    typer.echo("generating program_id.py...")
    gen_program_id(idl_obj, program_id_to_use, out)
    typer.echo("generating errors.py...")
    gen_errors(idl_obj, out)
    typer.echo("generating instructions...")
    gen_instructions(idl_obj, out)
    typer.echo("generating types...")
    gen_types(idl_obj, out)
    typer.echo("generating accounts...")
    gen_accounts(idl_obj, out)


if __name__ == "__main__":
    app()
