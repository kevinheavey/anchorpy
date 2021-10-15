from anchorpy.coder.coder import Coder
from anchorpy.program.namespace.namespace import build_namespace
from anchorpy.idl import Idl
from anchorpy.provider import Provider
from solana.publickey import PublicKey


class Program(object):
    """Program provides the IDL deserialized client representation of an Anchor program.

    This API is the one stop shop for all things related to communicating with
    on-chain programs. Among other things, one can send transactions, fetch
    deserialized accounts, decode instruction data, subscribe to account
    changes, and listen to events.

    In addition to field accessors and methods, the object provides a set of
    dynamically generated properties, also known as namespaces, that
    map one-to-one to program methods and accounts.

    """

    def __init__(self, idl: Idl, program_id: PublicKey, provider: Provider):
        self.idl = idl
        self.program_id = program_id
        self.provider = provider
        self.coder = Coder(idl)

        rpc, instruction, transaction, account, simulate = build_namespace(
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
