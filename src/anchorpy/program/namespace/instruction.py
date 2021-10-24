from typing import Callable, List, Any, Sequence, cast, Tuple

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


class InstructionFn:
    def __init__(
        self,
        idl_ix: IdlInstruction,
        encode_fn: Callable[[Instruction], bytes],
        program_id: PublicKey,
    ) -> None:
        """Callable object to create a `TransactionInstruction` generated from an IDL.

        Additionally it provides an `accounts` utility method, returning a list
        of ordered accounts for the instruction.
        """
        if idl_ix.name == "_inner":
            raise ValueError("_inner name is reserved")
        self.idl_ix = idl_ix
        self.encode_fn = encode_fn
        self.program_id = program_id

    def accounts(self, accs: Accounts) -> List[AccountMeta]:
        """Utility fn for ordering the accounts for this instruction."""
        return accounts_array(accs, self.idl_ix.accounts)

    def __call__(
        self, *args: Any, ctx: Context = EMPTY_CONTEXT
    ) -> TransactionInstruction:
        """Create the TransactionInstruction.

        Args:
            *args: The positional arguments for the program. The type and number
                of these arguments depend on the program being used.
            ctx: non-argument parameters to pass to the method.
        """
        check_args_length(self.idl_ix, args)
        validate_accounts(self.idl_ix.accounts, ctx.accounts)
        validate_instruction(self.idl_ix, args)

        keys = self.accounts(ctx.accounts)
        if ctx.remaining_accounts:
            keys.extend(ctx.remaining_accounts)
        return TransactionInstruction(
            keys=keys,
            program_id=self.program_id,
            data=self.encode_fn(to_instruction(self.idl_ix, args)),
        )


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
