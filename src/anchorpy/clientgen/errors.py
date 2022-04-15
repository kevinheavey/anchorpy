from pathlib import Path
from genpy import (
    FromImport,
    Suite,
    Return,
    Assign,
    If,
    For,
    Import,
    Class,
    Function as UntypedFunction,
    Statement,
)
from anchorpy.idl import Idl, _IdlErrorCode
from .utils import Function, TypedParam, Try, Break, Union


def gen_from_code_fn(has_custom_errors: bool) -> Function:
    from_code_body = Return(
        "custom.from_code(code) if code >= 6000 else anchor.from_code(code)"
        if has_custom_errors
        else "anchor.from_code(code)"
    )
    from_code_return_type = (
        Union(["custom.CustomError", "anchor.AnchorError", "None"])
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


def gen_custom_errors_code(errors: list[_IdlErrorCode]) -> str:
    typing_import = FromImport("typing", ["Union", "Optional"])
    error_import = FromImport("anchorpy.error", ["ProgramError"])
    error_names = [err.name for err in errors]
    error_union = Union(error_names)
    type_alias = Assign("CustomError", error_union)
    classes: list[Class] = []
    for error in errors:
        maybe_msg = error.msg
        msg = None if maybe_msg is None else f'"{maybe_msg}"'
        init_body = Statement(f"super().__init__({error.code}, {msg})")
        attrs = [
            UntypedFunction("__init__", ["self"], init_body),
            Assign("code", error.code),
            Assign("name", f'"{error.name}"'),
            Assign("msg", msg),
        ]
        klass = Class(name=error.name, bases=["ProgramError"], attributes=attrs)
        classes.append(klass)
    error_map = Assign("ERROR_MAP", {error.code: error.name for error in errors})
    from_code_body = Suite(
        [
            Assign("maybe_err", "ERROR_MAP.get(code)"),
            If("maybe_err is None", Return("None")),
            Return("maybe_err()"),
        ]
    )
    from_code_fn = Function(
        "from_code",
        [TypedParam("code", "int")],
        from_code_body,
        "Optional[CustomError]",
    )
    return str(
        Suite(
            [typing_import, error_import, type_alias, *classes, error_map, from_code_fn]
        )
    )


def gen_custom_errors(idl: Idl, out: Path) -> None:
    errors = idl.errors
    if errors is None or not errors:
        return
    code = gen_custom_errors_code(errors)
    print("custom errors code!!!")
    print(code)


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
    print("index code!!!!")
    print(code)


def gen_errors(idl: Idl, out_path: Path) -> None:
    gen_index(idl, out_path)
    gen_custom_errors(idl, out_path)
