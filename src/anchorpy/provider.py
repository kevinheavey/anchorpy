from __future__ import annotations

from pathlib import Path
from os import getenv
import json
from jsonrpcclient import parse

from abc import abstractmethod, ABC
from typing import List, Optional, Union, NamedTuple

from solana.keypair import Keypair
from solana.rpc import types
from solana.rpc.api import Client
from solana.transaction import Transaction, TransactionSignature

from solana.publickey import PublicKey


class SendTxRequest(NamedTuple):
    tx: Transaction
    signers: List[Keypair]


class Provider:
    """The network and wallet context used to send transactions paid for and signed by the provider."""  # noqa: E501

    def __init__(
        self, client: Client, wallet: Wallet, opts: types.TxOpts = types.TxOpts()
    ) -> None:
        """Initialize the Provider.

        Args:
            client: The cluster connection where the program is deployed.
            wallet: The wallet used to pay for and sign all transactions.
            opts: Transaction confirmation options to use by default.
        """
        self.client = client
        self.wallet = wallet
        self.opts = opts

    def send(
        self,
        tx: Transaction,
        signers: Optional[List[Keypair]] = None,
        opts: types.TxOpts = None,
    ) -> TransactionSignature:
        """Send the given transaction, paid for and signed by the provider's wallet.

        Args:
            tx: The transaction to send.
            signers: The set of signers in addition to the provider wallet that will
                sign the transaction.
            opts: Transaction confirmation options.

        Returns:
            The transaction signature from the RPC server.
        """
        if signers is None:
            signers = []
        if opts is None:
            opts = self.opts
        all_signers = [self.wallet.payer] + signers
        return self.client.send_transaction(tx, *all_signers, opts=opts)["result"]

    def send_all(
        self,
        reqs: List[Union[Transaction, SendTxRequest]],
        opts: Optional[types.TxOpts] = None,
    ) -> List[TransactionSignature]:
        """Similar to `send`, but for an array of transactions and signers.

        Args:
            reqs: a list of Transaction or SendTxRequest objects.
                Use SendTxRequest to specify additional signers other than the wallet.
            opts: Transaction confirmation options.

        Returns:
            The transaction signatures from the RPC server.
        """
        if opts is None:
            opts = self.opts
        txs = []
        for req in reqs:
            signers = [] if isinstance(req, Transaction) else req.signers
            tx = req if isinstance(req, Transaction) else req.tx
            for signer in signers:
                tx.sign_partial(signer)
            txs.append(tx)
        signed_txs = self.wallet.sign_all_transactions(txs)
        sigs = []
        for signed in signed_txs:
            res = self.client.send_raw_transaction(signed.serialize(), opts=opts)
            sigs.append(res["result"])
        return sigs


class Wallet(ABC):
    """Abstract base class for wallets."""

    def __init__(self, payer: Keypair):
        """Init."""
        self.payer = payer

    @property
    @abstractmethod
    def public_key(self) -> PublicKey:
        """Must return the public key of the wallet."""

    @abstractmethod
    def sign_transaction(self, tx: Transaction) -> Transaction:
        """Sign a transaction using the wallet's keypair.

        Args:
            tx: The transaction to sign.

        Returns:
            The signed transaction.
        """

    @abstractmethod
    def sign_all_transactions(self, txs: List[Transaction]):
        """Must implement signing multiple transactions."""


class LocalWallet(Wallet):
    """Python wallet object."""

    @property
    def public_key(self) -> PublicKey:
        """Get the public key of the wallet."""
        return self.payer.public_key

    def sign_transaction(self, tx: Transaction) -> Transaction:
        """Sign a transaction using the wallet's keypair.

        Args:
            tx: The transaction to sign.

        Returns:
            The signed transaction.
        """
        tx.sign(self.payer)
        return tx

    def sign_all_transactions(self, txs: List[Transaction]) -> List[Transaction]:
        """Sign a list of transactions using the wallet's keypair.

        Args:
            txs: The transactions to sign.

        Returns:
            The signed transactions.
        """
        for tx in txs:
            tx.sign_partial(self.payer)
        return txs

    @classmethod
    def local(cls) -> LocalWallet:
        """Create a wallet instance from the filesystem.

        Uses the path at the ANCHOR_WALLET env var if set,
        otherwise uses ~/.config/solana/id.json.
        """
        path = Path(getenv("ANCHOR_WALLET", Path.home() / ".config/solana/id.json"))
        with path.open() as f:
            keypair = json.load(f)
        return cls(Keypair.from_secret_key(keypair))
