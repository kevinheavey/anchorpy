from typing import Callable, List, Any, Sequence, cast, Tuple

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
) -> InstructionFn:
    if idl_ix.name == "_inner":
        raise ValueError("_inner name is reserved")

    def instruction_method(*args) -> TransactionInstruction:
        def accounts(accs: Accounts) -> List[AccountMeta]:
            return accounts_array(accs, idl_ix.accounts)

        split_args, ctx = split_args_and_context(idl_ix, args)
        validate_accounts(idl_ix.accounts, ctx.accounts)
        validate_instruction(idl_ix, split_args)

        keys = accounts(ctx.accounts)
        if ctx.remaining_accounts:
            keys.extend(ctx.remaining_accounts)
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
    # TODO: this isn't implemented in the TS client yet
    pass


if __name__ == "__main__":
    from anchorpy.idl import Idl
    from pathlib import Path
    from json import load
    from solana.keypair import Keypair

    with (Path.home() / "anchorpy/idls/composite.json").open() as f:
        idl_json = load(f)
    idl = Idl.from_json(idl_json)
    dummyA = Keypair.generate()
    dummyB = Keypair.generate()
    comp_accounts = {
        "foo": {
            "dummyA": dummyA.public_key,
        },
        "bar": {
            "dummyB": dummyB.public_key,
        },
    }
    accounts_arg = idl.instructions[1].accounts
    acc_arr = accounts_array(comp_accounts, accounts_arg)
    assert acc_arr == [
        AccountMeta(pubkey=dummyA.public_key, is_signer=False, is_writable=True),
        AccountMeta(pubkey=dummyB.public_key, is_signer=False, is_writable=True),
    ]
