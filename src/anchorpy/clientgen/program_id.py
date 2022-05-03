from pathlib import Path
from black import format_str, FileMode
from genpy import Assign, FromImport, Collection
from anchorpy.idl import Idl


def gen_program_id_code(idl: Idl, program_id: str) -> str:
    import_line = FromImport("solana.publickey", ["PublicKey"])
    assignment_line = Assign("PROGRAM_ID", f'PublicKey("{program_id}")')
    return str(Collection([import_line, assignment_line]))


def gen_program_id(idl: Idl, program_id: str, root: Path) -> None:
    code = gen_program_id_code(idl, program_id)
    formatted = format_str(code, mode=FileMode())
    (root / "program_id.py").write_text(formatted)
