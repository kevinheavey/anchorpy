from typing import List, Any, Optional
from dataclasses import dataclass
from solana.transaction import TransactionInstruction, AccountMeta, Transaction
from solana.keypair import Keypair
from solana.rpc import types
from solders.signature import Signature
from anchorpy.program.context import Context, Accounts
from anchorpy.program.namespace.rpc import _RpcFn
from anchorpy.program.namespace.simulate import _SimulateFn
from anchorpy.program.namespace.transaction import _TransactionFn
from anchorpy.program.namespace.instruction import _InstructionFn
from anchorpy.program.namespace.simulate import SimulateResponse


@dataclass
class IdlFuncs:
    ix_fn: _InstructionFn
    tx_fn: _TransactionFn
    rpc_fn: _RpcFn
    simulate_fn: _SimulateFn


class MethodsBuilder:
    def __init__(
        self,
        idl_funcs: IdlFuncs,
        accounts: Accounts,
        remaining_accounts: List[AccountMeta],
        signers: List[Keypair],
        pre_instructions: List[TransactionInstruction],
        post_instructions: List[TransactionInstruction],
        args: List[Any],
    ) -> None:
        self._idl_funcs = idl_funcs
        self._accounts = accounts
        self._remaining_accounts = remaining_accounts
        self._signers = signers
        self._pre_instructions = pre_instructions
        self._post_instructions = post_instructions
        self._args = args

    async def rpc(self, opts: Optional[types.TxOpts] = None) -> Signature:
        ctx = self._build_context(opts)
        return await self._idl_funcs.rpc_fn(*self._args, ctx=ctx)

    async def simulate(self, opts: Optional[types.TxOpts] = None) -> SimulateResponse:
        ctx = self._build_context(opts)
        return await self._idl_funcs.simulate_fn(*self._args, ctx=ctx)

    def instruction(self) -> TransactionInstruction:
        ctx = self._build_context(opts=None)
        return self._idl_funcs.ix_fn(*self._args, ctx=ctx)

    def transaction(self) -> Transaction:
        ctx = self._build_context(opts=None)
        return self._idl_funcs.tx_fn(*self._args, ctx=ctx)

    def pubkeys(self) -> Accounts:
        return self._accounts

    def args(self, arguments: List[Any]) -> "MethodsBuilder":
        idl_funcs = self._idl_funcs
        return MethodsBuilder(
            idl_funcs=idl_funcs,
            accounts=self._accounts,
            remaining_accounts=self._remaining_accounts,
            signers=self._signers,
            pre_instructions=self._pre_instructions,
            post_instructions=self._post_instructions,
            args=arguments,
        )

    def accounts(self, accs: Accounts) -> "MethodsBuilder":
        idl_funcs = self._idl_funcs
        return MethodsBuilder(
            idl_funcs=idl_funcs,
            accounts=accs,
            remaining_accounts=self._remaining_accounts,
            signers=self._signers,
            pre_instructions=self._pre_instructions,
            post_instructions=self._post_instructions,
            args=self._args,
        )

    def signers(self, signers: List[Keypair]) -> "MethodsBuilder":
        idl_funcs = self._idl_funcs
        return MethodsBuilder(
            idl_funcs=idl_funcs,
            accounts=self._accounts,
            remaining_accounts=self._remaining_accounts,
            signers=self._signers + signers,
            pre_instructions=self._pre_instructions,
            post_instructions=self._post_instructions,
            args=self._args,
        )

    def remaining_accounts(self, accounts: List[AccountMeta]) -> "MethodsBuilder":
        idl_funcs = self._idl_funcs
        return MethodsBuilder(
            idl_funcs=idl_funcs,
            accounts=self._accounts,
            remaining_accounts=self._remaining_accounts + accounts,
            signers=self._signers,
            pre_instructions=self._pre_instructions,
            post_instructions=self._post_instructions,
            args=self._args,
        )

    def pre_instructions(self, ixs: List[TransactionInstruction]) -> "MethodsBuilder":
        idl_funcs = self._idl_funcs
        return MethodsBuilder(
            idl_funcs=idl_funcs,
            accounts=self._accounts,
            remaining_accounts=self._remaining_accounts,
            signers=self._signers,
            pre_instructions=self._pre_instructions + ixs,
            post_instructions=self._post_instructions,
            args=self._args,
        )

    def post_instructions(self, ixs: List[TransactionInstruction]) -> "MethodsBuilder":
        idl_funcs = self._idl_funcs
        return MethodsBuilder(
            idl_funcs=idl_funcs,
            accounts=self._accounts,
            remaining_accounts=self._remaining_accounts,
            signers=self._signers,
            pre_instructions=self._pre_instructions,
            post_instructions=self._post_instructions + ixs,
            args=self._args,
        )

    def _build_context(self, opts: Optional[types.TxOpts]) -> Context:
        return Context(
            accounts=self._accounts,
            remaining_accounts=self._remaining_accounts,
            signers=self._signers,
            pre_instructions=self._pre_instructions,
            post_instructions=self._post_instructions,
            options=opts,
        )


def _build_methods_item(idl_funcs: IdlFuncs) -> MethodsBuilder:
    return MethodsBuilder(
        idl_funcs=idl_funcs,
        accounts={},
        remaining_accounts=[],
        signers=[],
        pre_instructions=[],
        post_instructions=[],
        args=[],
    )
