from pathlib import Path
from genpy import FromImport, Suite, Return
from anchorpy.idl import Idl
from .utils import Function, TypedParam


def gen_index_code(idl: Idl) -> str:
    has_custom_errors = idl.errors and len(idl.errors) > 0
    union_import = FromImport("typing", ["Union", "Optional"])
    program_id_import = FromImport(".program_id", ["PROGRAM_ID"])
    anchor_import = FromImport(".", ["anchor"])
    base_import_lines = [union_import, program_id_import, anchor_import]
    custom_import_lines = [FromImport(".", ["custom"])] if has_custom_errors else []
    import_lines = base_import_lines + custom_import_lines
    from_code_body = Return(
        "custom.from_code(code) if code >= 6000 else anchor.from_code(code)"
        if has_custom_errors
        else "anchor.from_code(code)"
    )
    from_code_return_type = (
        "Union[custom.CustomError, anchor.AnchorError, None]"
        if has_custom_errors
        else "Optional[anchor.AnchorError]"
    )
    from_code_fn = Function(
        "from_code", [TypedParam("code", "int")], from_code_body, from_code_return_type
    )
    return str(Suite(import_lines + [from_code_fn]))


def gen_index(idl: Idl, out_path: Path) -> None:
    code = gen_index_code(idl)
    print(code)


def gen_errors(idl: Idl, out_path: Path) -> None:
    gen_index(idl, out_path)
