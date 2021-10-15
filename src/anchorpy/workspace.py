from typing import Dict, cast
from json import load
from pathlib import Path
from solana.publickey import PublicKey
from anchorpy.program.core import Program
from anchorpy.provider import Provider
from anchorpy.idl import Idl, Metadata


def create_workspace() -> Dict[str, Program]:
    """Get a workspace from the current working directory."""

    result = {}
    project_root = Path.cwd()
    idl_folder = project_root / "target/idl"
    for file in idl_folder.iterdir():
        with file.open() as f:
            idl_dict = load(f)
        idl = Idl.from_json(idl_dict)
        metadata = cast(Metadata, idl.metadata)
        program = Program(idl, PublicKey(metadata.address), Provider.local())
        result[idl.name] = program
    return result


async def close_workspace(workspace: Dict[str, Program]) -> None:
    """Close the HTTP clients of all the programs in the workspace."""
    for program in workspace.values():
        # could do this in a faster way but there's probably no point.
        await program.close()
