from typing import Callable, List, Any, Sequence, cast, Tuple, Protocol

from solana.transaction import TransactionInstruction, AccountMeta
from solana.publickey import PublicKey

from anchorpy.program.common import (
    to_instruction,
    validate_accounts,
    translate_address,
    Instruction,
)
from anchorpy.program.context import EMPTY_CONTEXT, Context, check_args_length, Accounts
from anchorpy.idl import IdlInstruction, IdlAccountItem, IdlAccounts, IdlAccount


class InstructionFn(Protocol):
    """Function to create a `TransactionInstruction` generated from an IDL.

    Additionally it provides an `accounts` utility method, returning a list
    of ordered accounts for the instruction.
    """

    def __call__(
        self,
        *args: Any,
        ctx: Context = EMPTY_CONTEXT,
    ) -> TransactionInstruction:
        """

        Args:
            *args: The positional arguments for the program. The type and number
                of these arguments depend on the program being used.
            ctx: non-argument parameters to pass to the method.
        """
        ...


def build_instruction_fn(  # ts: InstructionNamespaceFactory.build
    idl_ix: IdlInstruction,
    encode_fn: Callable[[Instruction], bytes],
    program_id: PublicKey,
) -> InstructionFn:
    if idl_ix.name == "_inner":
        raise ValueError("_inner name is reserved")

    def instruction_method(
        *args: Any,
        ctx: Context = EMPTY_CONTEXT,
    ) -> TransactionInstruction:
        def accounts(accs: Accounts) -> List[AccountMeta]:
            return accounts_array(accs, idl_ix.accounts)

        check_args_length(idl_ix, args)
        validate_accounts(idl_ix.accounts, ctx.accounts)
        validate_instruction(idl_ix, args)

        keys = accounts(ctx.accounts)
        if ctx.remaining_accounts:
            keys.extend(ctx.remaining_accounts)
        return TransactionInstruction(
            keys=keys,
            program_id=program_id,
            data=encode_fn(to_instruction(idl_ix, args)),
        )

    return instruction_method


def accounts_array(
    ctx: Accounts,
    accounts: Sequence[IdlAccountItem],
) -> List[AccountMeta]:
    accounts_ret: List[AccountMeta] = []
    for acc in accounts:
        if isinstance(acc, IdlAccounts):
            rpc_accs = cast(Accounts, ctx[acc.name])
            acc_arr = accounts_array(rpc_accs, acc.accounts)
            accounts_ret.extend(acc_arr)
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


def validate_instruction(ix: IdlInstruction, args: Tuple):
    """Throws error if any argument required for the `ix` is not given."""
    # TODO: this isn't implemented in the TS client yet
    pass
