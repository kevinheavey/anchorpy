from typing import Dict, Optional, cast
from json import load
from pathlib import Path
from solana.publickey import PublicKey
from anchorpy.program.core import Program
from anchorpy.provider import Provider
from anchorpy.idl import Idl, Metadata


def create_workspace(
    path: Optional[Path] = None, url: Optional[str] = None
) -> Dict[str, Program]:
    """Get a workspace from the provided path to the project root.

    Args:
        path: The path to the project root. Defaults to the current working
            directory if omitted.
        url: The URL of the JSON RPC. Defaults to http://localhost:8899.

    Returns:
        Mapping of program name to Program object.
    """

    result = {}
    project_root = Path.cwd() if path is None else path
    idl_folder = project_root / "target/idl"
    for file in idl_folder.iterdir():
        with file.open() as f:
            idl_dict = load(f)
        idl = Idl.from_json(idl_dict)
        metadata = cast(Metadata, idl.metadata)
        program = Program(idl, PublicKey(metadata.address), Provider.local(url))
        result[idl.name] = program
    return result


async def close_workspace(workspace: Dict[str, Program]) -> None:
    """Close the HTTP clients of all the programs in the workspace."""
    for program in workspace.values():
        # could do this in a faster way but there's probably no point.
        await program.close()
