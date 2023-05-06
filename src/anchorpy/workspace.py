"""This module contains code for creating the Anchor workspace."""
from pathlib import Path
from typing import Dict, Optional, Union

import toml  # type: ignore
from anchorpy_core.idl import Idl
from solders.pubkey import Pubkey

from anchorpy.program.core import Program
from anchorpy.provider import Provider

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
    localnet_programs: dict[str, str] = toml.load(project_root / "Anchor.toml")[
        "programs"
    ]["localnet"]
    for file in idl_folder.iterdir():
        raw = file.read_text()
        idl = Idl.from_json(raw)
        name = idl.name
        program_id = Pubkey.from_string(localnet_programs[name])
        program = Program(idl, program_id, Provider.local(url))
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
