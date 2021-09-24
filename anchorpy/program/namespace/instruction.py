import itertools
from typing import Callable, List, Any, Sequence, cast, get_args

from solana.transaction import TransactionInstruction, AccountMeta

from anchorpy.program.common import (
    to_instruction,
    validate_accounts,
    translate_address,
    InstructionToSerialize,
)
from anchorpy.program.context import split_args_and_context, Accounts
from solana.publickey import PublicKey
from anchorpy.idl import IdlInstruction, IdlAccountItem, IdlAccounts, IdlAccount

InstructionEncodeFn = Callable[[str, str], List[bytes]]

InstructionFn = Callable[[Any], Any]


def build_instruction_fn(  # ts: InstructionNamespaceFactory.build
    idl_ix: IdlInstruction,
    encode_fn: Callable[[InstructionToSerialize], bytes],
    program_id: PublicKey,
    accounts_method=None,
) -> InstructionFn:
    if idl_ix.name == "_inner":
        raise ValueError("_inner name is reserved")

    def instruction_method(*args) -> TransactionInstruction:
        def accounts(accs: Accounts) -> List[AccountMeta]:
            return accounts_array(accs, idl_ix.accounts)

        arg_list = list(args)
        split_args, ctx = split_args_and_context(idl_ix, arg_list)
        validate_accounts(idl_ix.accounts, ctx.accounts)
        validate_instruction(idl_ix, split_args)

        keys = (
            accounts_method(ctx.accounts) if accounts_method else accounts(ctx.accounts)
        )
        if ctx.remaining_accounts:
            keys.append(ctx.remaining_accounts)
        return TransactionInstruction(
            keys=keys,
            program_id=program_id,
            data=encode_fn(to_instruction(idl_ix, split_args)),
        )

    return instruction_method


def accounts_array(
    ctx: Accounts, accounts: Sequence[IdlAccountItem]
) -> List[AccountMeta]:
    accounts_ret: List[AccountMeta] = []
    for acc in accounts:
        if isinstance(acc, get_args(IdlAccounts)):
            rpc_accs = cast(Accounts, ctx[acc.name])
            acc_arr = accounts_array(rpc_accs, acc.accounts)
            to_append: List[AccountMeta] = list(
                itertools.chain.from_iterable(acc_arr),  # type: ignore
            )
            accounts_ret.extend(to_append)
        else:
            account: IdlAccount = acc
            accounts_ret.append(
                AccountMeta(
                    pubkey=translate_address(ctx[account.name]),
                    is_writable=account.is_mut,
                    is_signer=account.is_signer,
                )
            )
    return accounts_ret


def validate_instruction(ix: IdlInstruction, args: List[Any]):
    # TODO
    pass
