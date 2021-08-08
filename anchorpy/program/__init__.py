from anchorpy.coder.coder import Coder
from anchorpy.program.namespace.namespace import NamespaceFactory
from anchorpy.idl import Idl
from anchorpy.provider import Provider
from anchorpy.public_key import PublicKey


class Program(object):
    def __init__(self, idl: Idl, program_id: PublicKey, provider: Provider):
        self._idl = idl
        self._program_id = program_id
        self._provider = provider
        self._coder = Coder(idl)

        rpc, instruction, transaction, account, simulate, state = NamespaceFactory.build(self._idl, self._coder,
                                                                                         program_id, self._provider)

        self.rpc = rpc
        self.instruction = instruction
        self.transaction = transaction
        self.account = account
        self.simulate = simulate
        self.state = state

    @property
    def program_id(self) -> PublicKey:
        return self._program_id

    @property
    def provider(self) -> Provider:
        return self._provider

    @property
    def idl(self) -> Idl:
        return self._idl

    @property
    def coder(self) -> Coder:
        return self._coder
