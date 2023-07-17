from pathlib import Path
from typing import Optional, Union, cast

from anchorpy_core.idl import (
    Idl,
    IdlAccountItem,
    IdlAccounts,
    IdlSeedConst,
    IdlTypeArray,
    IdlTypeSimple,
)
from autoflake import fix_code
from black import FileMode, format_str
from genpy import (
    Assign,
    Collection,
    FromImport,
    If,
    Import,
    ImportAs,
    Line,
    Return,
    Suite,
)
from pyheck import shouty_snake, snake, upper_camel

from anchorpy.clientgen.common import (
    _field_to_encodable,
    _layout_for_type,
    _py_type_from_idl,
    _sanitize,
)
from anchorpy.clientgen.genpy_extension import (
    ANNOTATIONS_IMPORT,
    Call,
    Function,
    List,
    NamedArg,
    StrDict,
    StrDictEntry,
    TypedDict,
    TypedParam,
)
from anchorpy.coder.common import _sighash
from anchorpy.coder.idl import FIELD_TYPE_MAP

CONST_ACCOUNTS = {
    "associated_token_program": "ASSOCIATED_TOKEN_PROGRAM_ID",
    "rent": "RENT",
    "system_program": "SYS_PROGRAM_ID",
    "token_program": "TOKEN_PROGRAM_ID",
    "clock": "CLOCK",
}


def gen_instructions(idl: Idl, root: Path, gen_pdas: bool) -> None:
    instructions_dir = root / "instructions"
    instructions_dir.mkdir(exist_ok=True)
    gen_index_file(idl, instructions_dir)
    instructions = gen_instructions_code(idl, instructions_dir, gen_pdas)
    for path, code in instructions.items():
        formatted = format_str(code, mode=FileMode())
        fixed = fix_code(formatted, remove_all_unused_imports=True)
        path.write_text(fixed)


def gen_index_file(idl: Idl, instructions_dir: Path) -> None:
    code = gen_index_code(idl)
    path = instructions_dir / "__init__.py"
    formatted = format_str(code, mode=FileMode())
    path.write_text(formatted)


def gen_index_code(idl: Idl) -> str:
    imports: list[FromImport] = []
    for ix in idl.instructions:
        ix_name_snake_unsanitized = snake(ix.name)
        ix_name = _sanitize(ix_name_snake_unsanitized)
        import_members: list[str] = [ix_name]
        if ix.args:
            import_members.append(_args_interface_name(ix_name_snake_unsanitized))
        if ix.accounts:
            import_members.append(_accounts_interface_name(ix_name_snake_unsanitized))
        if import_members:
            imports.append(FromImport(f".{ix_name}", import_members))
    return str(Collection(imports))


def _args_interface_name(ix_name: str) -> str:
    return f"{upper_camel(ix_name)}Args"


def _accounts_interface_name(ix_name: str) -> str:
    return f"{upper_camel(ix_name)}Accounts"


def recurse_accounts(
    accs: list[IdlAccountItem],
    nested_names: list[str],
    const_accs: dict[int, str],
    acc_idx: int = 0,
) -> tuple[list[str], int]:
    elements: list[str] = []
    for acc in accs:
        names = [*nested_names, _sanitize(snake(acc.name))]
        if isinstance(acc, IdlAccounts):
            nested_accs = cast(IdlAccounts, acc)
            new_elements, acc_idx = recurse_accounts(
                nested_accs.accounts, names, const_accs, acc_idx
            )
            elements.extend(new_elements)
        else:
            acc_idx += 1
            try:
                pubkey_var = const_accs[acc_idx]
            except KeyError:
                try:
                    pubkey_var = CONST_ACCOUNTS[names[-1]]
                except KeyError:
                    nested_keys = [f'["{key}"]' for key in names]
                    dict_accessor = "".join(nested_keys)
                    pubkey_var = f"accounts{dict_accessor}"
            if acc.is_optional:
                elements.append(
                    f"AccountMeta(pubkey={pubkey_var}, "
                    f"is_signer={acc.is_signer}, "
                    f"is_writable={acc.is_mut}) "
                    f"if {pubkey_var} else AccountMeta(pubkey=program_id, is_signer=False, is_writable=False)"
                )
            else:
                elements.append(
                    f"AccountMeta(pubkey={pubkey_var}, "
                    f"is_signer={acc.is_signer}, "
                    f"is_writable={acc.is_mut})"
                )
    return elements, acc_idx


def to_buffer_value(
    ty: Union[IdlTypeSimple, IdlTypeArray], value: Union[str, int, list[int]]
) -> bytes:
    if isinstance(value, int):
        encoder = FIELD_TYPE_MAP[cast(IdlTypeSimple, ty)]
        return encoder.build(value)
    if isinstance(value, str):
        return value.encode()
    if isinstance(value, list):
        return bytes(value)
    raise ValueError(f"Unexpected type. ty: {ty}; value: {value}")


GenAccountsRes = tuple[list[TypedDict], list[Assign], dict[int, str], int]


def gen_accounts(
    name,
    idl_accs: list[IdlAccountItem],
    gen_pdas: bool,
    accum: Optional[GenAccountsRes] = None,
) -> GenAccountsRes:
    if accum is None:
        extra_typeddicts_to_use: list[TypedDict] = []
        accum_const_pdas: list[Assign] = []
        const_acc_indices: dict[int, str] = {}
        acc_count = 0
    else:
        extra_typeddicts_to_use, accum_const_pdas, const_acc_indices, acc_count = accum
    params: list[TypedParam] = []
    const_pdas: list[Assign] = []
    for acc in idl_accs:
        acc_name = _sanitize(snake(acc.name))
        if isinstance(acc, IdlAccounts):
            nested_accs = cast(IdlAccounts, acc)
            nested_acc_name = f"{upper_camel(nested_accs.name)}Nested"
            nested_res = gen_accounts(
                nested_acc_name,
                nested_accs.accounts,
                gen_pdas,
                (
                    extra_typeddicts_to_use,
                    accum_const_pdas,
                    const_acc_indices,
                    acc_count,
                ),
            )
            if nested_res[0]:
                params.append(TypedParam(acc_name, f"{nested_acc_name}"))
            extra_typeddicts_to_use = extra_typeddicts_to_use + nested_res[0]
            accum_const_pdas = accum_const_pdas + nested_res[1]
            const_acc_indices = const_acc_indices | nested_res[2]
            acc_count = nested_res[3] + 1
        else:
            acc_count += 1
            pda_generated = False
            if gen_pdas:
                maybe_pda = acc.pda
                if maybe_pda is not None and all(
                    isinstance(seed, IdlSeedConst) for seed in maybe_pda.seeds
                ):
                    seeds = cast(list[IdlSeedConst], maybe_pda.seeds)
                    const_pda_name = shouty_snake(f"{name}_{acc_name}")
                    const_pda_body_items = [
                        str(
                            to_buffer_value(
                                cast(Union[IdlTypeSimple, IdlTypeArray], seed.ty),
                                cast(Union[str, int, list[int]], seed.value),
                            )
                        )
                        for seed in seeds
                    ]
                    seeds_arg = List(const_pda_body_items)
                    seeds_named_arg = NamedArg("seeds", seeds_arg)
                    const_pda_body = Call(
                        "Pubkey.find_program_address",
                        [seeds_named_arg, NamedArg("program_id", "PROGRAM_ID")],
                    )
                    const_pdas.append(Assign(const_pda_name, f"{const_pda_body}[0]"))
                    const_acc_indices = {
                        **const_acc_indices,
                        acc_count: const_pda_name,
                    }
                    pda_generated = True
            if not pda_generated:
                try:
                    CONST_ACCOUNTS[acc_name]
                except KeyError:
                    if acc.is_optional:
                        params.append(TypedParam(acc_name, "typing.Optional[Pubkey]"))
                    else:
                        params.append(TypedParam(acc_name, "Pubkey"))
    maybe_typed_dict_container = [TypedDict(name, params)] if params else []
    accounts = maybe_typed_dict_container + extra_typeddicts_to_use
    return accounts, accum_const_pdas + const_pdas, const_acc_indices, acc_count


def gen_instructions_code(idl: Idl, out: Path, gen_pdas: bool) -> dict[Path, str]:
    types_import = [FromImport("..", ["types"])] if idl.types else []
    imports = [
        ANNOTATIONS_IMPORT,
        Import("typing"),
        FromImport("solders.pubkey", ["Pubkey"]),
        FromImport("solders.system_program", ["ID as SYS_PROGRAM_ID"]),
        FromImport("solders.sysvar", ["RENT", "CLOCK"]),
        FromImport(
            "spl.token.constants", ["TOKEN_PROGRAM_ID", "ASSOCIATED_TOKEN_PROGRAM_ID"]
        ),
        FromImport("solders.instruction", ["Instruction", "AccountMeta"]),
        FromImport(
            "anchorpy.borsh_extension", ["BorshPubkey", "EnumForCodegen", "COption"]
        ),
        FromImport("construct", ["Pass", "Construct"]),
        ImportAs("borsh_construct", "borsh"),
        *types_import,
        FromImport("..program_id", ["PROGRAM_ID"]),
    ]
    result = {}
    for ix in idl.instructions:
        ix_name_snake_unsanitized = snake(ix.name)
        ix_name = _sanitize(ix_name_snake_unsanitized)
        filename = (out / ix_name).with_suffix(".py")
        args_interface_params: list[TypedParam] = []
        layout_items: list[str] = []
        encoded_args_entries: list[StrDictEntry] = []
        accounts_interface_name = _accounts_interface_name(ix_name_snake_unsanitized)
        for arg in ix.args:
            arg_name = _sanitize(snake(arg.name))
            args_interface_params.append(
                TypedParam(
                    arg_name,
                    _py_type_from_idl(
                        idl=idl,
                        ty=arg.ty,
                        types_relative_imports=False,
                        use_fields_interface_for_struct=False,
                    ),
                )
            )
            layout_items.append(
                _layout_for_type(
                    idl=idl, ty=arg.ty, name=arg_name, types_relative_imports=False
                )
            )
            encoded_args_entries.append(
                StrDictEntry(
                    arg_name,
                    _field_to_encodable(
                        idl=idl,
                        ty=arg,
                        types_relative_imports=False,
                        val_prefix='args["',
                        val_suffix='"]',
                    ),
                )
            )
        if ix.args:
            args_interface_name = _args_interface_name(ix_name)
            args_interface_container = [
                TypedDict(args_interface_name, args_interface_params)
            ]
            layout_val = f"borsh.CStruct({','.join(layout_items)})"
            layout_assignment_container = [Assign("layout", layout_val)]
            args_container = [TypedParam("args", args_interface_name)]
            encoded_args_val = f"layout.build({StrDict(encoded_args_entries)})"
        else:
            args_interface_container = []
            layout_val = "Pass"
            args_container = []
            layout_assignment_container = []
            encoded_args_val = 'b""'
        accounts_container = (
            [TypedParam("accounts", accounts_interface_name)] if ix.accounts else []
        )
        accounts, const_pdas, const_acc_indices, _ = gen_accounts(
            accounts_interface_name, ix.accounts, gen_pdas
        )
        recursed = recurse_accounts(ix.accounts, [], const_acc_indices)[0]
        keys_assignment = Assign("keys: list[AccountMeta]", f"{List(recursed)}")
        remaining_accounts_concatenation = If(
            "remaining_accounts is not None", Line("keys += remaining_accounts")
        )
        identifier_assignment = Assign(
            "identifier", _sighash(ix_name_snake_unsanitized)
        )
        encoded_args_assignment = Assign("encoded_args", encoded_args_val)
        data_assignment = Assign("data", "identifier + encoded_args")
        returning = Return("Instruction(program_id, data, keys)")
        ix_fn = Function(
            ix_name,
            [
                *args_container,
                *accounts_container,
                TypedParam("program_id", "Pubkey = PROGRAM_ID"),
                TypedParam(
                    "remaining_accounts",
                    "typing.Optional[typing.List[AccountMeta]] = None",
                ),
            ],
            Suite(
                [
                    keys_assignment,
                    remaining_accounts_concatenation,
                    identifier_assignment,
                    encoded_args_assignment,
                    data_assignment,
                    returning,
                ]
            ),
            "Instruction",
        )
        contents = Collection(
            [
                *imports,
                *args_interface_container,
                *layout_assignment_container,
                *const_pdas,
                *accounts,
                ix_fn,
            ]
        )
        result[filename] = str(contents)
    return result
