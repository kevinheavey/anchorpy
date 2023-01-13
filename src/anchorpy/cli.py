import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, cast

import typer
from anchorpy_core.idl import Idl
from IPython import embed

from anchorpy import create_workspace
from anchorpy.clientgen.accounts import gen_accounts
from anchorpy.clientgen.errors import gen_errors
from anchorpy.clientgen.instructions import gen_instructions
from anchorpy.clientgen.program_id import gen_program_id
from anchorpy.clientgen.types import gen_types
from anchorpy.template import INIT_TESTS

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
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)


def _search_upwards_for_project_root() -> Path:
    """Search in the current dir and all directories above it for an Anchor.toml file.

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
    """AnchorPy CLI."""


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


@app.command()
def client_gen(
    idl: Path = typer.Argument(..., help="Anchor IDL file path"),
    out: Path = typer.Argument(..., help="Output directory."),
    program_id: Optional[str] = typer.Option(
        None, help="Optional program ID to be included in the code"
    ),
    pdas: bool = typer.Option(
        False, "--pdas", help="Auto-generate PDAs where possible."
    ),
):
    """Generate Python client code from the specified anchor IDL."""
    idl_obj = Idl.from_json(idl.read_text())
    if program_id is None:
        idl_metadata = idl_obj.metadata
        address_from_idl = (
            idl_metadata["address"] if isinstance(idl_metadata, dict) else None
        )
        if address_from_idl is None:
            typer.echo(
                "No program ID found in IDL. Use the --program-id "
                "option to set it manually."
            )
            raise typer.Exit(code=1)
        else:
            program_id_to_use = cast(str, address_from_idl)
    else:
        program_id_to_use = program_id

    typer.echo("generating package...")
    out.mkdir(exist_ok=True)
    (out / "__init__.py").touch()
    typer.echo("generating program_id.py...")
    gen_program_id(program_id_to_use, out)
    typer.echo("generating errors.py...")
    gen_errors(idl_obj, out)
    typer.echo("generating instructions...")
    gen_instructions(idl_obj, out, pdas)
    typer.echo("generating types...")
    gen_types(idl_obj, out)
    typer.echo("generating accounts...")
    gen_accounts(idl_obj, out)


if __name__ == "__main__":
    app()
