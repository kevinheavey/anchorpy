import itertools
from typing import Callable, List, Any

from solana.transaction import TransactionInstruction, AccountMeta

from anchorpy.program.common import to_instruction, validate_accounts, translate_address
from anchorpy.program.context import split_args_and_context, Accounts
from anchorpy.public_key import PublicKey
from anchorpy.idl import IdlInstruction, IdlAccountItem, IdlAccounts, IdlAccount

InstructionEncodeFn = Callable[[str, str], List[bytes]]

InstructionFn = Callable[[Any], Any]


class IdlError(Exception):
    pass


class InstructionNamespace(object):
    pass


class InstructionNamespaceFactory(object):
    @staticmethod
    def build(idl_ix: IdlInstruction,
              encode_fn: Callable[[str, Any], bytes],
              program_id: PublicKey,
              accounts_method = None) -> InstructionFn:
        if idl_ix.name == "_inner":
            raise IdlError("_inner name is reserved")

        def instruction_method(*args) -> TransactionInstruction:
            def accounts(accs: Accounts) -> List[AccountMeta]:
                return InstructionNamespaceFactory.accounts_array(accs, idl_ix.accounts)

            args = list(args)
            args, ctx = split_args_and_context(idl_ix, args)
            validate_accounts(idl_ix.accounts, ctx.accounts)
            validate_instruction(idl_ix, args)

            keys = accounts_method(ctx.accounts) if accounts_method else accounts(ctx.accounts)
            if ctx.remaining_accounts:
                keys.append(ctx.remaining_accounts)
            return TransactionInstruction(keys=keys,
                                          program_id=program_id,
                                          data=encode_fn(idl_ix.name, to_instruction(idl_ix, args)))

        return instruction_method

    @staticmethod
    def accounts_array(ctx: Accounts, accounts: List[IdlAccountItem]) -> List[AccountMeta]:
        accounts_ret = []
        for acc in accounts:
            if isinstance(acc, IdlAccounts):
                rpc_accs = ctx[acc.name]
                accounts_ret.append(
                    list(itertools.chain(*InstructionNamespaceFactory.accounts_array(rpc_accs, acc.accounts))))
            else:
                account: IdlAccount = acc
                accounts_ret.append(AccountMeta(pubkey=translate_address(ctx[acc.name]),
                                                is_writable=account.is_mut,
                                                is_signer=account.is_signer))
        return accounts_ret


def validate_instruction(ix: IdlInstruction, args: List[Any]):
    # TODO
    pass
