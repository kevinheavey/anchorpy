from __future__ import annotations

import base64
import functools
from types import SimpleNamespace
from typing import Dict, Tuple, Optional, Any, List

import inflection as inflection
from solana.system_program import SYS_PROGRAM_ID
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.transaction import AccountMeta

from anchorpy.coder.state import state_discriminator
from anchorpy.program.context import Accounts
from anchorpy.program.common import parse_idl_errors, validate_accounts
from anchorpy.coder.coder import Coder
from anchorpy.program.namespace.instruction import InstructionNamespace, InstructionNamespaceFactory
from anchorpy.program.namespace.rpc import RpcNamespace, RpcNamespaceFactory
from anchorpy.program.namespace.transaction import TransactionNamespace, TransactionNamespaceFactory
from anchorpy.public_key import PublicKey

from anchorpy.idl import Idl, IdlStateMethod
from anchorpy.provider import Provider


def encode_fn(coder: Coder, ix_name: str, ix: Any) -> bytes:
    return coder.instruction.encode_state(ix_name, ix)


def accounts_method(program_id, provider, m, accounts: Accounts):
    keys = state_instruction_keys(program_id, provider, m, accounts)
    return keys + InstructionNamespaceFactory.accounts_array(accounts, m.accounts)


class StateClient(object):
    def __init__(self,
                 idl: Idl,
                 program_id: PublicKey,
                 provider: Provider,
                 coder: Coder):
        self._idl = idl
        self._program_id = program_id
        self._address = program_state_address(program_id)
        self._provider = provider
        self._coder = coder

        instruction, transaction, rpc = self._build_namespace()

        # Namespace stuff so you can do state.rpc.method()
        self.rpc = rpc
        self.instruction = instruction
        self.transaction = transaction

    def _build_namespace(self) -> Tuple[InstructionNamespace, TransactionNamespace, RpcNamespace]:
        instruction = InstructionNamespace()
        transaction = TransactionNamespace()
        rpc = RpcNamespace()

        for m in self._idl.state.methods:
            ix_item = InstructionNamespaceFactory.build(m,
                                                        functools.partial(encode_fn, self._coder),
                                                        self.program_id,
                                                        functools.partial(accounts_method, self.program_id,
                                                                          self.provider, m))

            tx_item = TransactionNamespaceFactory.build(m, ix_item)
            rpc_item = RpcNamespaceFactory.build(m, tx_item, parse_idl_errors(self._idl), self.provider)

            name = inflection.camelize(m.name, False)

            setattr(instruction, name, ix_item)
            setattr(transaction, name, tx_item)
            setattr(rpc, name, rpc_item)

        return instruction, transaction, rpc

    @property
    def program_id(self) -> PublicKey:
        """Returns the program ID owning the state."""
        return self._program_id

    @property
    def provider(self) -> Provider:
        """Returns the client's wallet and network provider."""
        return self._provider

    @property
    def coder(self) -> Coder:
        """Returns the coder"""
        return self._coder

    @property
    def address(self) -> PublicKey:
        return self._address

    def fetch(self) -> SimpleNamespace:
        """Fetches state from the blockchain"""
        account_info = self.provider.get_account_info(self.address)

        if not account_info["result"]["value"]:
            raise Exception("Account does not exist")
        account_data = base64.b64decode(account_info["result"]["value"]["data"][0])
        expected_discriminator = state_discriminator(self._idl.state.struct.name)
        if expected_discriminator != account_data[:8]:
            raise Exception("Invalid account discriminator")
        state = self.coder.state.decode(account_data)[1]

        return state

    def subscribe(self) -> Any:
        pass

    def unsubscribe(self) -> Any:
        pass


class StateFactory(object):
    @staticmethod
    def build(idl: Idl, coder: Coder, program_id: PublicKey, provider: Provider) -> Optional[StateClient]:
        if not idl.state:
            return None
        return StateClient(idl, program_id, provider, coder)


def program_state_address(program_id: PublicKey) -> PublicKey:
    registry_signer = PublicKey.find_program_address([], program_id)
    return PublicKey.create_with_seed(registry_signer[0], "unversioned", program_id)


def state_instruction_keys(program_id: PublicKey,
                           provider: Provider,
                           m: IdlStateMethod,
                           accounts: Accounts) -> List[AccountMeta]:
    """
    Returns the common keys that are prepended to all instructions targeting the "state" of a program.
    """
    if m.name == "new":
        program_signer, _ = PublicKey.find_program_address([], program_id)
        return [AccountMeta(pubkey=provider.wallet.public_key, is_writable=False, is_signer=True),
                AccountMeta(pubkey=program_state_address(program_id), is_writable=True, is_signer=False),
                AccountMeta(pubkey=program_signer, is_writable=False, is_signer=False),
                AccountMeta(pubkey=SYS_PROGRAM_ID, is_writable=False, is_signer=False),
                AccountMeta(pubkey=program_id, is_writable=False, is_signer=False),
                AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_writable=False, is_signer=False)]
    else:
        validate_accounts(m.accounts, accounts)
        return [AccountMeta(pubkey=program_state_address(program_id), is_writable=True,
                            is_signer=False)]
