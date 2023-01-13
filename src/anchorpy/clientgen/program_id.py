from pathlib import Path

from black import FileMode, format_str
from genpy import Assign, Collection, FromImport


def gen_program_id_code(program_id: str) -> str:
    import_line = FromImport("solders.pubkey", ["Pubkey"])
    assignment_line = Assign("PROGRAM_ID", f'Pubkey.from_string("{program_id}")')
    return str(Collection([import_line, assignment_line]))


def gen_program_id(program_id: str, root: Path) -> None:
    code = gen_program_id_code(program_id)
    formatted = format_str(code, mode=FileMode())
    (root / "program_id.py").write_text(formatted)
