"""This module contains the Provider class and associated utilities."""
from __future__ import annotations

import json
from os import environ, getenv
from pathlib import Path
from types import MappingProxyType
from typing import List, Optional, Sequence, Union

from solana.rpc import types
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Finalized, Processed
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.rpc.responses import SimulateTransactionResp
from solders.signature import Signature
from solders.transaction import VersionedTransaction

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
        tx: Union[Transaction, VersionedTransaction],
        opts: Optional[types.TxOpts] = None,
    ) -> SimulateTransactionResp:
        """Simulate the given transaction, returning emitted logs from execution.

        Args:
            tx: The transaction to send.
            signers: The set of signers in addition to the provider wallet that will
                sign the transaction.
            opts: Transaction confirmation options.

        Returns:
            The transaction simulation result.
        """
        if opts is None:
            opts = self.opts
        return await self.connection.simulate_transaction(
            tx, sig_verify=True, commitment=opts.preflight_commitment
        )

    async def send(
        self,
        tx: Union[Transaction, VersionedTransaction],
        opts: Optional[types.TxOpts] = None,
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
        if opts is None:
            opts = self.opts
        raw = tx.serialize() if isinstance(tx, Transaction) else bytes(tx)
        resp = await self.connection.send_raw_transaction(raw, opts=opts)
        return resp.value

    async def send_all(
        self,
        txs: Sequence[Union[Transaction, VersionedTransaction]],
        opts: Optional[types.TxOpts] = None,
    ) -> list[Signature]:
        """Similar to `send`, but for an array of transactions and signers.

        Args:
            txs: a list of transaction objects.
            opts: Transaction confirmation options.

        Returns:
            The transaction signatures from the RPC server.
        """
        if opts is None:
            opts = self.opts
        sigs = []
        for tx in txs:
            raw = tx.serialize() if isinstance(tx, Transaction) else bytes(tx)
            resp = await self.connection.send_raw_transaction(raw, opts=opts)
            sigs.append(resp.value)
        return sigs

    async def __aenter__(self) -> Provider:
        """Use as a context manager."""
        await self.connection.__aenter__()
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
    def public_key(self) -> Pubkey:
        """Get the public key of the wallet."""
        return self.payer.pubkey()

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
            keypair: List[int] = json.load(f)
        return cls(Keypair.from_bytes(keypair))

    @classmethod
    def dummy(cls) -> Wallet:
        """Create a dummy wallet instance that won't be used to sign transactions."""
        keypair = Keypair()
        return cls(keypair)
