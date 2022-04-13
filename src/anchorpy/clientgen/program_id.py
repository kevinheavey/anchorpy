from typing import Optional
from pathlib import Path
from genpy import Assign, FromImport, Suite
from anchorpy.idl import Idl


def gen_program_id_code(idl: Idl, program_id: str) -> str:
    import_line = FromImport("solana.publickey", ["PublicKey"])
    assignment_line = Assign("PROGRAM_ID", f'PublicKey({"program_id"})')
    return str(Suite([import_line, assignment_line]))


def gen_program_id(idl: Idl, program_id: str, out_path: Path) -> None:
    code = gen_program_id_code(idl, program_id)
    print(code)
