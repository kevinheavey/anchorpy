from typing import Optional
import typer
from IPython import embed
from anchorpy import create_workspace

app = typer.Typer()


@app.callback()
def callback():
    """AnchorPy CLI."""  # noqa: D403


@app.command()
def shell(path: Optional[str] = None):
    """Start an IPython shell with an AnchorPy workspace object initialized."""
    workspace = create_workspace()  # noqa: F841
    embed(
        colors="neutral",
        using="asyncio",
        banner2="Hint: type `workspace` to see the Anchor workspace object.\n",
    )


if __name__ == "__main__":
    app()
