"""This module deals with generating program instructions."""
from typing import Callable, Any, Sequence, cast, Tuple

from solana.transaction import TransactionInstruction, AccountMeta
from solana.publickey import PublicKey

from anchorpy.program.common import (  # noqa: WPS347
    _to_instruction,
    validate_accounts,
    translate_address,
    Instruction,
)
from anchorpy.program.context import (
    EMPTY_CONTEXT,
    Context,
    _check_args_length,
    Accounts,
)
from anchorpy.idl import _IdlInstruction, _IdlAccountItem, _IdlAccounts, _IdlAccount


class _InstructionFn:
    """Callable object to create a `TransactionInstruction` generated from an IDL.

    Additionally it provides an `accounts` utility method, returning a list
    of ordered accounts for the instruction.
    """

    def __init__(
        self,
        idl_ix: _IdlInstruction,
        encode_fn: Callable[[Instruction], bytes],
        program_id: PublicKey,
    ) -> None:
        """Init.

        Args:
            idl_ix: IDL instruction object
            encode_fn: [description]
            program_id: The program ID.

        Raises:
            ValueError: [description]
        """
        if idl_ix.name == "_inner":
            raise ValueError("_inner name is reserved")
        self.idl_ix = idl_ix
        self.encode_fn = encode_fn
        self.program_id = program_id

    def __call__(
        self,
        *args: Any,
        ctx: Context = EMPTY_CONTEXT,
    ) -> TransactionInstruction:
        """Create the TransactionInstruction.

        Args:
            *args: The positional arguments for the program. The type and number
                of these arguments depend on the program being used.
            ctx: non-argument parameters to pass to the method.
        """
        _check_args_length(self.idl_ix, args)
        validate_accounts(self.idl_ix.accounts, ctx.accounts)
        _validate_instruction(self.idl_ix, args)

        keys = self.accounts(ctx.accounts)
        if ctx.remaining_accounts:
            keys.extend(ctx.remaining_accounts)
        return TransactionInstruction(
            keys=keys,
            program_id=self.program_id,
            data=self.encode_fn(_to_instruction(self.idl_ix, args)),
        )

    def accounts(self, accs: Accounts) -> list[AccountMeta]:
        """Order the accounts for this instruction.

        Args:
            accs: Accounts from `ctx` kwarg.

        Returns:
            Ordered and flattened accounts.
        """
        return _accounts_array(accs, self.idl_ix.accounts)


def _accounts_array(
    ctx: Accounts,
    accounts: Sequence[_IdlAccountItem],
) -> list[AccountMeta]:
    """Create a list of AccountMeta from a (possibly nested) dict of accounts.

    Args:
        ctx: `accounts` field from the `Context` object.
        accounts: accounts from the IDL.

    Returns:
        AccountMeta objects.
    """
    accounts_ret: list[AccountMeta] = []
    for acc in accounts:
        if isinstance(acc, _IdlAccounts):
            rpc_accs = cast(Accounts, ctx[acc.name])
            acc_arr = _accounts_array(rpc_accs, acc.accounts)
            accounts_ret.extend(acc_arr)
        else:
            account: _IdlAccount = acc
            accounts_ret.append(
                AccountMeta(
                    pubkey=translate_address(ctx[account.name]),
                    is_writable=account.is_mut,
                    is_signer=account.is_signer,
                ),
            )
    return accounts_ret


def _validate_instruction(ix: _IdlInstruction, args: Tuple):
    """Throws error if any argument required for the `ix` is not given.

    Args:
        ix: The IDL instruction object.
        args: The instruction arguments.
    """
    # TODO: this isn't implemented in the TS client yet
