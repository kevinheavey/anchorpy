"""This module contains the Provider class and associated utilities."""
from __future__ import annotations

from pathlib import Path
from os import getenv, environ
import json
from types import MappingProxyType
from typing import List, Optional, Union, NamedTuple

from solders.rpc.responses import SimulateTransactionResp
from solders.signature import Signature
from more_itertools import unique_everseen
from solana.keypair import Keypair
from solana.rpc import types
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Finalized, Processed, Confirmed
from solana.transaction import Transaction
from solana.publickey import PublicKey
from solana.blockhash import Blockhash


class SendTxRequest(NamedTuple):
    """Use this to provide custom signers to `Provider.send_all`.

    Attributes:
        tx: The Transaction to send.
        signers: Custom signers for the transaction.
    """

    tx: Transaction
    signers: List[Keypair]


DEFAULT_OPTIONS = types.TxOpts(skip_confirmation=False, preflight_commitment=Processed)
COMMITMENT_RANKS = MappingProxyType({Processed: 0, Confirmed: 1, Finalized: 2})


class Provider:
    """The network and wallet context used to send transactions paid for and signed by the provider."""  # noqa: E501

    def __init__(
        self,
        connection: AsyncClient,
        wallet: Wallet,
        opts: types.TxOpts = DEFAULT_OPTIONS,
    ) -> None:
        """Initialize the Provider.

        Args:
            connection: The cluster connection where the program is deployed.
            wallet: The wallet used to pay for and sign all transactions.
            opts: Transaction confirmation options to use by default.
        """
        self.connection = connection
        self.wallet = wallet
        self.opts = opts

    @classmethod
    def local(
        cls, url: Optional[str] = None, opts: types.TxOpts = DEFAULT_OPTIONS
    ) -> Provider:
        """Create a `Provider` with a wallet read from the local filesystem.

        Args:
            url: The network cluster url.
            opts: The default transaction confirmation options.
        """
        connection = AsyncClient(url, opts.preflight_commitment)
        wallet = Wallet.local()
        return cls(connection, wallet, opts)

    @classmethod
    def readonly(
        cls, url: Optional[str] = None, opts: types.TxOpts = DEFAULT_OPTIONS
    ) -> Provider:
        """Create a `Provider` that can only fetch data, not send transactions.

        Args:
            url: The network cluster url.
            opts: The default transaction confirmation options.
        """
        connection = AsyncClient(url, opts.preflight_commitment)
        wallet = Wallet.dummy()
        return cls(connection, wallet, opts)

    @classmethod
    def env(cls) -> Provider:
        """Create a `Provider` using the `ANCHOR_PROVIDER_URL` environment variable."""
        url = environ["ANCHOR_PROVIDER_URL"]
        options = DEFAULT_OPTIONS
        connection = AsyncClient(url, options.preflight_commitment)
        wallet = Wallet.local()
        return cls(connection, wallet, options)

    async def simulate(
        self,
        tx: Transaction,
        signers: Optional[list[Keypair]] = None,
        opts: types.TxOpts = None,
    ) -> SimulateTransactionResp:
        """Simulate the given transaction, returning emitted logs from execution.

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
        recent_blockhash_resp = await self.connection.get_latest_blockhash(
            Finalized,
        )
        tx.recent_blockhash = Blockhash(str(recent_blockhash_resp.value.blockhash))
        tx.fee_payer = self.wallet.public_key
        all_signers = list(unique_everseen([self.wallet.payer, *signers]))
        tx.sign(*all_signers)
        return await self.connection.simulate_transaction(
            tx, sig_verify=True, commitment=opts.preflight_commitment
        )

    async def send(
        self,
        tx: Transaction,
        signers: Optional[list[Keypair]] = None,
        opts: types.TxOpts = None,
    ) -> Signature:
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
        tx.fee_payer = self.wallet.public_key
        all_signers = list(unique_everseen([self.wallet.payer, *signers]))
        resp = await self.connection.send_transaction(tx, *all_signers, opts=opts)
        return resp.value

    async def send_all(
        self,
        reqs: list[Union[Transaction, SendTxRequest]],
        opts: Optional[types.TxOpts] = None,
    ) -> list[Signature]:
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
            tx.fee_payer = self.wallet.public_key
            for signer in signers:
                tx.sign_partial(signer)
            txs.append(tx)
        signed_txs = self.wallet.sign_all_transactions(txs)
        sigs = []
        for signed in signed_txs:
            resp = await self.connection.send_raw_transaction(
                signed.serialize(), opts=opts
            )
            sigs.append(resp.value)
        return sigs

    async def __aenter__(self) -> Provider:
        """Use as a context manager."""
        await self.connection.__aenter__()  # noqa: WPS609
        return self

    async def __aexit__(self, _exc_type, _exc, _tb):
        """Exit the context manager."""
        await self.close()

    async def close(self) -> None:
        """Use this when you are done with the connection."""
        await self.connection.close()


class Wallet:
    """Python wallet object."""

    def __init__(self, payer: Keypair):
        """Initialize the wallet.

        Args:
            payer: the Keypair used to sign transactions.
        """
        self.payer = payer

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

    def sign_all_transactions(self, txs: list[Transaction]) -> list[Transaction]:
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
    def local(cls) -> Wallet:
        """Create a wallet instance from the filesystem.

        Uses the path at the ANCHOR_WALLET env var if set,
        otherwise uses ~/.config/solana/id.json.
        """
        path = Path(getenv("ANCHOR_WALLET", Path.home() / ".config/solana/id.json"))
        with path.open() as f:
            keypair = json.load(f)
        return cls(Keypair.from_secret_key(bytes(keypair)))

    @classmethod
    def dummy(cls) -> Wallet:
        """Create a dummy wallet instance that won't be used to sign transactions."""
        keypair = Keypair.from_secret_key(bytes([0] * 64))  # noqa: WPS435
        return cls(keypair)
