"""This module contains code for creating the Anchor workspace."""
from typing import Optional, Union, cast, Dict
import json
from pathlib import Path
from solana.publickey import PublicKey
from anchorpy.program.core import Program
from anchorpy.provider import Provider
from anchorpy.idl import Idl, _Metadata

WorkspaceType = Dict[str, Program]


def create_workspace(
    path: Optional[Union[Path, str]] = None, url: Optional[str] = None
) -> WorkspaceType:
    """Get a workspace from the provided path to the project root.

    Args:
        path: The path to the project root. Defaults to the current working
            directory if omitted.
        url: The URL of the JSON RPC. Defaults to http://localhost:8899.

    Returns:
        Mapping of program name to Program object.
    """
    result = {}
    project_root = Path.cwd() if path is None else Path(path)
    idl_folder = project_root / "target/idl"
    for file in idl_folder.iterdir():
        with file.open() as f:
            idl_dict = json.load(f)
        idl = Idl.from_json(idl_dict)
        metadata = cast(_Metadata, idl.metadata)
        program = Program(idl, PublicKey(metadata.address), Provider.local(url))
        result[idl.name] = program
    return result


async def close_workspace(workspace: WorkspaceType) -> None:
    """Close the HTTP clients of all the programs in the workspace.

    Args:
        workspace: The workspace to close.
    """
    for program in workspace.values():
        # could do this in a faster way but there's probably no point.
        await program.close()
