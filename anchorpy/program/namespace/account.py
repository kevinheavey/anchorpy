import base64
from types import SimpleNamespace
from typing import List, Optional, Dict, Callable

import inflection
from solana.account import Account
from solana.system_program import create_account, CreateAccountParams
from solana.transaction import TransactionInstruction
from solana.rpc.commitment import Processed

from anchorpy.coder.common import account_size

from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE, account_discriminator
from anchorpy.coder.coder import Coder
from anchorpy.idl import Idl, IdlTypeDef
from anchorpy.provider import Provider
from solana.publickey import PublicKey


def build_account(
    idl: Idl, coder: Coder, program_id: PublicKey, provider: Provider
) -> Dict[str, "AccountClient"]:
    accounts_fns = {}
    for idl_account in idl.accounts:
        account_client = AccountClient(idl, idl_account, coder, program_id, provider)
        accounts_fns[idl_account.name] = account_client
    return accounts_fns


class AccountDoesNotExistError(Exception):
    pass


class AccountInvalidDiscriminator(Exception):
    pass


class AccountClient(object):
    def __init__(
        self,
        idl: Idl,
        idl_account: IdlTypeDef,
        coder: Coder,
        program_id: PublicKey,
        provider: Provider,
    ):
        self._idl_account = idl_account
        self._program_id = program_id
        self._provider = provider
        self._coder = coder
        self._size = ACCOUNT_DISCRIMINATOR_SIZE + account_size(idl, idl_account)

    def fetch(self, address: PublicKey) -> SimpleNamespace:
        account_info = self._provider.get_account_info(
            address, encoding="base64", commitment=Processed
        )
        if not account_info["result"]["value"]:
            raise AccountDoesNotExistError(f"Account {address} does not exist")
        data = base64.b64decode(account_info["result"]["value"]["data"][0])
        discriminator = account_discriminator(self._idl_account.name)
        if discriminator != data[:8]:
            raise AccountInvalidDiscriminator(
                f"Account {address} has an invalid discriminator"
            )
        return self._coder.accounts.decode(self._idl_account.name, data)

    def create_instruction(
        self, signer: Account, size_override: int = 0
    ) -> TransactionInstruction:
        space = size_override if size_override else self._size
        return create_account(
            CreateAccountParams(
                from_pubkey=self._provider.wallet.public_key,
                new_account_pubkey=signer.public_key(),
                space=space,
                lamports=self._provider.get_minimum_balance_for_rent_exemption(space)[
                    "result"
                ],
                program_id=self._program_id,
            )
        )

    def associated_address(self, *args: PublicKey) -> PublicKey:
        seeds = b"anchor"
        for arg in args:
            seeds += bytes(arg)
        assoc = PublicKey.find_program_address([seeds], self._program_id)[0]
        return assoc

    def associated(self, *args: PublicKey) -> SimpleNamespace:
        addr = self.associated_address(*args)
        return self.fetch(addr)

    def all(self, filter: Optional[bytes] = None) -> List[Dict]:
        all_accounts = list()

        b = account_discriminator(self._idl_account.name)
        if filter:
            b = b + filter

        # TODO: use memcmp_opts here, something fucked up
        resp = self._provider.get_program_accounts(
            self._program_id,
            commitment=Processed,
            encoding="base64",
        )
        for r in resp["result"]:
            account_data = r["account"]["data"][0]
            account_data = bytes(base64.b64decode(account_data))
            if account_data.startswith(b):
                all_accounts.append(
                    {
                        "public_key": PublicKey(r["pubkey"]),
                        "account": self._coder.accounts.decode(
                            self._idl_account.name, account_data
                        ),
                    }
                )
        return all_accounts
