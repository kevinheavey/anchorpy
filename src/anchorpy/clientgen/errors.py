from pathlib import Path
from black import format_str, FileMode
from autoflake import fix_code
from genpy import (
    FromImport,
    Suite,
    Collection,
    Return,
    Assign,
    If,
    For,
    Import,
    Function as UntypedFunction,
    Statement,
)
from anchorpy.idl import Idl, _IdlErrorCode
from anchorpy.error import _LangErrorCode, LangErrorMessage
from anchorpy.clientgen.genpy_extension import (
    Function,
    TypedParam,
    Try,
    Union,
    InitMethod,
    Class,
    IntDict,
    IntDictEntry,
)


def gen_from_code_fn(has_custom_errors: bool) -> Function:
    from_code_body = Return(
        "custom.from_code(code) if code >= 6000 else anchor.from_code(code)"
        if has_custom_errors
        else "anchor.from_code(code)"
    )
    from_code_return_type = (
        Union(["custom.CustomError", "anchor.AnchorError", "None"])
        if has_custom_errors
        else "typing.Optional[anchor.AnchorError]"
    )
    return Function(
        "from_code",
        [TypedParam("code", "int")],
        from_code_body,
        str(from_code_return_type),
    )


def gen_find_first_match_fn() -> Function:
    regex_match = Assign("first_match", "error_re.match(logline)")
    return_if_match = If("first_match is not None", Return("first_match"))
    loop_body = Suite([regex_match, return_if_match])
    for_loop = For("logline", "logs", loop_body)
    return Function(
        "_find_first_match",
        [TypedParam("logs", "list[str]")],
        Suite([for_loop, Return("None")]),
        "typing.Optional[re.Match]",
    )


def gen_from_tx_error_fn(has_custom_errors: bool) -> Function:
    err_info_assign = Assign("err_info", "error.args[0]")
    has_data_block = If('"data" not in err_info', Return(None))
    has_logs_block = If('"logs" not in err_info["data"]', Return(None))
    no_match = If("first_match is None", Return("None"))
    assign_program_id_and_code = Assign(
        "program_id_raw, code_raw", "first_match.groups()"
    )
    program_id_check = If("program_id_raw != str(PROGRAM_ID)", Return("None"))
    parse_error_code = Try(
        Assign("error_code", "int(code_raw, 16)"), "ValueError", Return("None")
    )
    final_return = Return("from_code(error_code)")
    fn_body = Suite(
        [
            err_info_assign,
            has_data_block,
            has_logs_block,
            Assign("first_match", '_find_first_match(err_info["data"]["logs"])'),
            no_match,
            assign_program_id_and_code,
            program_id_check,
            parse_error_code,
            final_return,
        ]
    )
    return_type = (
        "typing.Union[anchor.AnchorError, custom.CustomError, None]"
        if has_custom_errors
        else "typing.Optional[anchor.AnchorError]"
    )
    return Function(
        "from_tx_error",
        [TypedParam("error", "RPCException")],
        fn_body,
        return_type,
    )


def gen_custom_errors_code(errors: list[_IdlErrorCode]) -> str:
    typing_import = Import("typing")
    error_import = FromImport("anchorpy.error", ["ProgramError"])
    error_names: list[str] = []
    classes: list[Class] = []
    error_map_entries: list[IntDictEntry] = []
    for error in errors:
        code = error.code
        name = error.name
        maybe_msg = error.msg
        msg = None if maybe_msg is None else f'"{maybe_msg}"'
        init_body = Statement(f"super().__init__({code}, {msg})")
        attrs = [
            InitMethod([], init_body),
            Assign("code", code),
            Assign("name", f'"{name}"'),
            Assign("msg", msg),
        ]
        klass = Class(name=name, bases=["ProgramError"], attributes=attrs)
        classes.append(klass)
        error_names.append(name)
        error_map_entries.append(IntDictEntry(code, f"{name}()"))
    type_alias = Assign("CustomError", Union(error_names))
    error_map = Assign(
        "CUSTOM_ERROR_MAP: dict[int, CustomError]", IntDict(error_map_entries)
    )
    from_code_body = Suite(
        [
            Assign("maybe_err", "CUSTOM_ERROR_MAP.get(code)"),
            If("maybe_err is None", Return("None")),
            Return("maybe_err"),
        ]
    )
    from_code_fn = Function(
        "from_code",
        [TypedParam("code", "int")],
        from_code_body,
        "typing.Optional[CustomError]",
    )
    return str(
        Collection(
            [typing_import, error_import, *classes, type_alias, error_map, from_code_fn]
        )
    )


def gen_custom_errors(idl: Idl, errors_dir: Path) -> None:
    errors = idl.errors
    if errors is None or not errors:
        return
    code = gen_custom_errors_code(errors)
    formatted = format_str(code, mode=FileMode())
    fixed = fix_code(formatted, remove_all_unused_imports=True)
    (errors_dir / "custom.py").with_suffix(".py").write_text(fixed)


def gen_anchor_errors_code() -> str:
    typing_import = Import("typing")
    error_import = FromImport("anchorpy.error", ["ProgramError"])
    error_names: list[str] = []
    classes: list[Class] = []
    error_map_entries: list[IntDictEntry] = []
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
        error_map_entries.append(IntDictEntry(code, f"{name}()"))
    type_alias = Assign("AnchorError", Union(error_names))
    error_map = Assign(
        "ANCHOR_ERROR_MAP: dict[int, AnchorError]",
        IntDict(error_map_entries),
    )
    from_code_body = Suite(
        [
            Assign("maybe_err", "ANCHOR_ERROR_MAP.get(code)"),
            If("maybe_err is None", Return("None")),
            Return("maybe_err"),
        ]
    )
    from_code_fn = Function(
        "from_code",
        [TypedParam("code", "int")],
        from_code_body,
        "typing.Optional[AnchorError]",
    )
    return str(
        Collection(
            [typing_import, error_import, *classes, type_alias, error_map, from_code_fn]
        )
    )


def gen_anchor_errors(errors_dir: Path) -> None:
    code = gen_anchor_errors_code()
    formatted = format_str(code, mode=FileMode())
    (errors_dir / "anchor").with_suffix(".py").write_text(formatted)


def gen_index_code(idl: Idl) -> str:
    has_custom_errors = bool(idl.errors)
    typing_import = Import("typing")
    rpc_exception_import = FromImport("solana.rpc.core", ["RPCException"])
    program_id_import = FromImport("..program_id", ["PROGRAM_ID"])
    anchor_import = FromImport(".", ["anchor"])
    re_import = Import("re")
    base_import_lines = [
        typing_import,
        re_import,
        rpc_exception_import,
        program_id_import,
        anchor_import,
    ]
    custom_import_lines = [FromImport(".", ["custom"])] if has_custom_errors else []
    import_lines = base_import_lines + custom_import_lines
    from_code_fn = gen_from_code_fn(has_custom_errors)
    error_re_line = Assign(
        "error_re", r're.compile(r"Program (\w+) failed: custom program error: (\w+)")'
    )
    from_tx_error_fn = gen_from_tx_error_fn(has_custom_errors)
    return str(
        Collection(
            [
                *import_lines,
                from_code_fn,
                error_re_line,
                gen_find_first_match_fn(),
                from_tx_error_fn,
            ]
        )
    )


def gen_index_file(idl: Idl, errors_dir: Path) -> None:
    code = gen_index_code(idl)
    path = errors_dir / "__init__.py"
    formatted = format_str(code, mode=FileMode())
    path.write_text(formatted)


def gen_errors(idl: Idl, root: Path) -> None:
    errors_dir = root / "errors"
    errors_dir.mkdir(exist_ok=True)
    gen_index_file(idl, errors_dir)
    gen_custom_errors(idl, errors_dir)
    gen_anchor_errors(errors_dir)
