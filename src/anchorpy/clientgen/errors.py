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
from anchorpy.error import _LangErrorCode, LangErrorMessage
from anchorpy.clientgen.utils import Function, TypedParam, Try, Break, Union


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
        "from_code", [TypedParam("code", "int")], from_code_body, str(from_code_return_type)
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
    error_names: list[str] = []
    classes: list[Class] = []
    error_map: dict[int, str] = {}
    for error in errors:
        code = error.code
        name = error.name
        maybe_msg = error.msg
        msg = None if maybe_msg is None else f'"{maybe_msg}"'
        init_body = Statement(f"super().__init__({code}, {msg})")
        attrs = [
            UntypedFunction("__init__", ["self"], init_body),
            Assign("code", code),
            Assign("name", f'"{name}"'),
            Assign("msg", msg),
        ]
        klass = Class(name=name, bases=["ProgramError"], attributes=attrs)
        classes.append(klass)
        error_names.append(name)
        error_map[code] = name
    type_alias = Assign("CustomError", Union(error_names))
    error_map = Assign("ANCHOR_ERROR_MAP", str(error_map).replace("'", ""))
    from_code_body = Suite(
        [
            Assign("maybe_err", "CUSTOM_ERROR_MAP.get(code)"),
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
            [typing_import, error_import, *classes, type_alias, error_map, from_code_fn]
        )
    )


def gen_custom_errors(idl: Idl, out: Path) -> None:
    errors = idl.errors
    if errors is None or not errors:
        return
    code = gen_custom_errors_code(errors)


def gen_anchor_errors_code() -> str:
    typing_import = FromImport("typing", ["Union"])
    error_import = FromImport("anchorpy.error", ["ProgramError"])
    error_names: list[str] = []
    classes: list[Class] = []
    error_map: dict[int, str] = {}
    for variant in _LangErrorCode:
        name = variant.name
        code = variant.value
        maybe_msg = LangErrorMessage.get(variant)
        msg = None if maybe_msg is None else f'"{maybe_msg}"'
        init_body = Statement(f"super().__init__({code}, {msg})")
        attrs = [
            UntypedFunction("__init__", ["self"], init_body),
            Assign("code", code),
            Assign("name", f'"{name}"'),
            Assign("msg", msg),
        ]
        klass = Class(name=name, bases=["ProgramError"], attributes=attrs)
        classes.append(klass)
        error_names.append(name)
        error_map[code] = name
    type_alias = Assign("AnchorError", Union(error_names))
    error_map = Assign("ANCHOR_ERROR_MAP", str(error_map).replace("'", ""))
    from_code_body = Suite(
        [
            Assign("maybe_err", "ANCHOR_ERROR_MAP.get(code)"),
            If("maybe_err is None", Return("None")),
            Return("maybe_err()"),
        ]
    )
    from_code_fn = Function(
        "from_code",
        [TypedParam("code", "int")],
        from_code_body,
        "Optional[AnchorError]",
    )
    return str(
        Suite(
            [typing_import, error_import, *classes, type_alias, error_map, from_code_fn]
        )
    )


def gen_anchor_errors(out: Path) -> None:
    code = gen_anchor_errors_code()


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


def gen_errors(idl: Idl, out_path: Path) -> None:
    gen_index(idl, out_path)
    gen_custom_errors(idl, out_path)
    gen_anchor_errors(out_path)
