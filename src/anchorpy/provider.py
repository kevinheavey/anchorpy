"""This module contains the Provider class and associated utilities."""
from __future__ import annotations

from pathlib import Path
from os import getenv, environ
import json
import asyncio
import time

from abc import abstractmethod, ABC
from typing import List, Optional, Union, NamedTuple, cast

from solana.keypair import Keypair
from solana.rpc import types
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Finalized, Processed, Confirmed, Commitment
from solana.rpc.core import RPCException
from solana.transaction import Transaction, TransactionSignature
from solana.publickey import PublicKey


class SendTxRequest(NamedTuple):
    tx: Transaction
    signers: List[Keypair]


DEFAULT_OPTIONS = types.TxOpts(skip_confirmation=False, preflight_commitment=Processed)
COMMITMENT_RANKS = {Processed: 0, Confirmed: 1, Finalized: 2}


class UnconfirmedTxError(Exception):
    """Raise when confirming a transaction times out."""


class Provider:
    """The network and wallet context used to send transactions paid for and signed by the provider."""  # noqa: E501

    def __init__(
        self, client: AsyncClient, wallet: Wallet, opts: types.TxOpts = DEFAULT_OPTIONS
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

    @classmethod
    def local(
        cls, url: Optional[str] = None, opts: types.TxOpts = DEFAULT_OPTIONS
    ) -> Provider:
        """Create a `Provider` with a wallet read from the local filesystem.

        Args:
            url: The network cluster url.
            opts: The default transaction confirmation options.
        """
        client = AsyncClient(url, opts.preflight_commitment)
        wallet = LocalWallet.local()
        return cls(client, wallet, opts)

    @classmethod
    def env(cls) -> Provider:
        """Create a `Provider` using the `ANCHOR_PROVIDER_URL` environment variable."""
        url = environ["ANCHOR_PROVIDER_URL"]
        options = DEFAULT_OPTIONS
        client = AsyncClient(url, options.preflight_commitment)
        wallet = LocalWallet.local()
        return cls(client, wallet, options)

    async def simulate(
        self,
        tx: Transaction,
        signers: Optional[List[Keypair]] = None,
        opts: types.TxOpts = None,
    ) -> types.RPCResponse:
        """Simulates the given transaction, returning emitted logs from execution.

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
        recent_blockhash_resp = await self.client.get_recent_blockhash(
            opts.preflight_commitment,
        )
        tx.recent_blockhash = recent_blockhash_resp["result"]["value"]["blockhash"]
        all_signers = [self.wallet.payer] + signers
        tx.sign(*all_signers)
        return await self.client.simulate_transaction(
            tx, sig_verify=True, commitment=opts.preflight_commitment
        )

    async def send(
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
        raw_resp = await self.client.send_transaction(
            tx, *all_signers, opts=opts._replace(skip_confirmation=True)
        )
        resp = cast(
            TransactionSignature,
            raw_resp["result"],
        )
        if opts.skip_preflight:
            return resp
        await self._confirm_transaction(resp, commitment=opts.preflight_commitment)
        return resp

    async def _confirm_transaction(
        self,
        tx_sig: str,
        commitment: Commitment = Finalized,
    ) -> types.RPCResponse:
        timeout = time.time() + 30
        while time.time() < timeout:
            resp = await self.client.get_signature_statuses([tx_sig])
            resp_value = resp["result"]["value"][0]
            if resp_value is not None:
                confirmation_status = resp_value["confirmationStatus"]
                confirmation_rank = COMMITMENT_RANKS[confirmation_status]
                commitment_rank = COMMITMENT_RANKS[commitment]
                if confirmation_rank >= commitment_rank:
                    break
            await asyncio.sleep(0.5)
        else:
            maybe_rpc_error = resp.get("error")
            if maybe_rpc_error is not None:
                raise RPCException(maybe_rpc_error)
            raise UnconfirmedTxError(f"Unable to confirm transaction {tx_sig}")
        return resp

    async def _send_raw_transaction(
        self, txn: Union[bytes, str], opts: types.TxOpts = DEFAULT_OPTIONS
    ) -> TransactionSignature:
        resp = await self.client.send_raw_transaction(
            txn, opts._replace(skip_confirmation=True)
        )
        signature = cast(
            TransactionSignature,
            resp["result"],
        )
        if opts.skip_confirmation:
            return signature
        self._confirm_transaction(signature, opts.preflight_commitment)
        return signature

    async def send_all(
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
            res = await self._send_raw_transaction(signed.serialize(), opts=opts)
            sigs.append(res)
        return sigs

    async def __aenter__(self) -> Provider:
        """Use as a context manager."""
        await self.client.__aenter__()  # noqa: WPS609
        return self

    async def __aexit__(self, _exc_type, _exc, _tb):
        """Exits the context manager."""
        await self.close()

    async def close(self) -> None:
        """Use this when you are done with the client."""
        await self.client.close()


class Wallet(ABC):
    """Abstract base class for wallets."""

    def __init__(self, payer: Keypair):
        """Initialize the wallet

        Args:
            payer: the Keypair used to sign transactions.
        """
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
        return cls(Keypair.from_secret_key(bytes(keypair)))
