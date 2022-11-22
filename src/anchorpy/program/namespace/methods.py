from typing import List, Any
from solders.rpc.responses import SimulateTransactionResp
from solana.transaction import TransactionInstruction, AccountMeta
from solana.keypair import Keypair
from anchorpy.program.context import Context, Accounts
from anchorpy.program.namespace.rpc import _RpcFn
from anchorpy.program.namespace.simulate import _SimulateFn
from anchorpy.program.namespace.transaction import _TransactionFn
from anchorpy.program.namespace.instruction import _InstructionFn

class MethodsBuilder:
    def __init__(
        self,
        ix_fn: _InstructionFn,
        tx_fn: _TransactionFn,
        rpc_fn: _RpcFn,
        simulate_fn: _SimulateFn,
        accounts: Accounts,
        remaining_accounts: List[AccountMeta],
        signers: List[Keypair],
        pre_instructions: List[TransactionInstruction],
        post_instructions: List[TransactionInstruction],
        args: List[Any],
    ) -> None:
        self.ix_fn = ix_fn
        self.tx_fn = tx_fn
        self.rpc_fn = rpc_fn
        self.simulate_fn = _SimulateFn
        self.accounts = {}
        self.remaining_accounts = []
        self.signers = []
        self.pre_instructions = []
        self.post_instructions = []
        self.args = []

    async def rpc(self, opts: Optional[types.TxOpts] = None) -> TransactionSignature:
        ctx = Context(options=opts)
        return await self.rpc_fn(self, *self.args, ctx=ctx)

    async def simulate(self, opts: Optional[types.TxOpts] = None) -> SimulateTransactionResp:
        ctx = Context(options=opts)
        return await self.simulate_fn(self, *self.args, ctx=ctx)


def _build_methods_item(
    ix_fn: _InstructionFn,
    tx_fn: _TransactionFn,
    rpc_fn: _RpcFn,
    simulate_fn: _SimulateFn,
) -> MethodsBuilder:
    return MethodsBuilder(
        ix_fn=ix_fn,
        tx_fn=tx_fn,
        rpc_fn=rpc_fn,
        simulate_fn=simulate_fn,
        remaining_accounts=[],
        signers=[],
        pre_instructions=[],
        post_instructions=[],
        args=[],
    )
