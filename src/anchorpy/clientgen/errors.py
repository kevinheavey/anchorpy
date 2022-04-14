from pathlib import Path
from genpy import FromImport, Suite, Return, Assign, If, For, Import
from anchorpy.idl import Idl
from .utils import Function, TypedParam, Try, Break


def gen_from_code_fn(has_custom_errors: bool) -> Function:
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
    return Function(
        "from_code", [TypedParam("code", "int")], from_code_body, from_code_return_type
    )


def gen_from_tx_error_fn() -> Function:
    has_logs_block = If('"logs" not in err', Return(None))
    regex_match = Assign("first_match", "error_re.match(logline)")
    break_if_match = If("first_match is not None", Break())
    loop_body = Suite([regex_match, break_if_match])
    for_loop = For("logline", 'err["logs"]', loop_body)
    no_match = If("first_match is None", Return("None"))
    assign_program_id_and_code = Assign(
        "program_id_raw, code_raw", "first_match.groups()"
    )
    program_id_check = If("program_id_raw != str(PROGRAM_ID)", Return("None"))
    parse_error_code = Try(
        Assign("error_code", "int(code_raw(16))"), "ValueError", Return("None")
    )
    final_return = Return("from_code(error_code)")
    fn_body = Suite(
        [
            has_logs_block,
            for_loop,
            no_match,
            assign_program_id_and_code,
            program_id_check,
            parse_error_code,
            final_return,
        ]
    )
    return Function(
        "from_tx_error",
        [TypedParam("error", "Any")],
        fn_body,
        "Optional[anchor.AnchorError]",
    )


def gen_index_code(idl: Idl) -> str:
    has_custom_errors = bool(idl.errors)
    typing_import = FromImport("typing", ["Union", "Optional", "Any"])
    program_id_import = FromImport(".program_id", ["PROGRAM_ID"])
    anchor_import = FromImport(".", ["anchor"])
    re_import = Import("re")
    base_import_lines = [typing_import, re_import, program_id_import, anchor_import]
    custom_import_lines = [FromImport(".", ["custom"])] if has_custom_errors else []
    import_lines = base_import_lines + custom_import_lines
    from_code_fn = gen_from_code_fn(has_custom_errors)
    error_re_line = Assign(
        "error_re", 're.compile("Program (\\w+) failed: custom program error: (\\w+)")'
    )
    from_tx_error_fn = gen_from_tx_error_fn()
    return str(Suite(import_lines + [from_code_fn, error_re_line, from_tx_error_fn]))


def gen_index(idl: Idl, out_path: Path) -> None:
    code = gen_index_code(idl)
    print(code)


def gen_errors(idl: Idl, out_path: Path) -> None:
    gen_index(idl, out_path)
