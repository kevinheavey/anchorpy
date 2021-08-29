from anchorpy.coder.coder import Coder
from anchorpy.program.namespace.namespace import build_namespace
from anchorpy.idl import Idl
from anchorpy.provider import Provider
from solana.publickey import PublicKey


class Program(object):
    def __init__(self, idl: Idl, program_id: PublicKey, provider: Provider):
        self.idl = idl
        self.program_id = program_id
        self.provider = provider
        self.coder = Coder(idl)

        rpc, instruction, transaction, account, simulate, state = build_namespace(
            idl,
            self.coder,
            program_id,
            provider,
        )

        self.rpc = rpc
        self.instruction = instruction
        self.transaction = transaction
        self.account = account
        self.simulate = simulate
        self.state = state
