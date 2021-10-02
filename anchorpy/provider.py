from __future__ import annotations

import json
from pathlib import Path

from abc import abstractmethod, ABC
from typing import List, Optional

from solana.keypair import Keypair
from solana.rpc import types
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment, Max
from solana.transaction import Transaction

from solana.publickey import PublicKey


class Provider:
    def __init__(
        self, client: Client, wallet: Wallet, opts: types.TxOpts = types.TxOpts()
    ):
        self.client = client
        self.wallet = wallet
        self.opts = opts

    def send(
        self,
        tx: Transaction,
        signers: Optional[List[Keypair]] = None,
        opts: types.TxOpts = None,
    ) -> types.RPCResponse:
        if signers is None:
            signers = []
        if opts is None:
            opts = self.opts
        all_signers = [self.wallet.payer] + signers
        return self.client.send_transaction(tx, *all_signers, opts=opts)


class Wallet(ABC):
    def __init__(self, payer: Keypair):
        self.payer = payer

    @property
    @abstractmethod
    def public_key(self) -> PublicKey:
        ...

    @abstractmethod
    def sign_transaction(self, tx: Transaction):
        pass

    @abstractmethod
    def sign_all_transactions(self, txs: List[Transaction]):
        pass


class NodeWallet(Wallet):
    @property
    def public_key(self) -> PublicKey:
        return self.payer.public_key

    def sign_transaction(self, tx: Transaction) -> Transaction:
        tx.sign(self.payer)
        return tx

    def sign_all_transactions(self, txs: List[Transaction]) -> List[Transaction]:
        for tx in txs:
            tx.sign_partial(self.payer)
        return txs

    @classmethod
    def local(cls) -> NodeWallet:
        fpath = Path.home() / ".config/solana/id.json"
        with fpath.open() as f:
            keypair = json.load(f)
        return cls(Keypair.from_secret_key(keypair))
