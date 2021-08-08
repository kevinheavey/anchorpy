from __future__ import annotations

import json
import os.path

from abc import abstractmethod, ABC, abstractproperty
from base64 import b64encode
from dataclasses import dataclass
import time
from typing import List, Optional, Union

from solana.blockhash import Blockhash
from solana.account import Account
from solana.rpc import types
from solana.rpc.api import Client
from solana.rpc.commitment import Single, Commitment, Max
from solana.transaction import Transaction

from anchorpy.public_key import PublicKey


class Provider(Client):
    def __init__(self, url, wallet: Wallet, opts=types.TxOpts()):
        super().__init__(url)
        self.wallet = wallet
        self.opts = opts

    def send(self,
             tx: Transaction,
             signers: Optional[List[Account]] = None,
             opts: types.TxOpts = None):
        if not signers:
            signers = []
        if not opts:
            opts = self.opts

        recent_blockhash = self.get_recent_blockhash(opts.preflight_commitment)["result"]["value"]["blockhash"]

        tx.fee_payer = self.wallet.account.public_key()
        tx.recent_blockhash = recent_blockhash
        self.wallet.sign_transaction(tx)
        tx.sign_partial(self.wallet.account, *signers)

        raw_tx = tx.serialize()
        tx_id = self.send_raw_transaction(raw_tx, opts)
        return tx_id

    def send_raw_transaction(self, txn: Union[bytes, str], opts: types.TxOpts = types.TxOpts()) -> types.RPCResponse:
        if isinstance(txn, bytes):
            txn = b64encode(txn).decode("utf-8")

        print(f"{time.time()} sending request", flush=True)
        resp = self._provider.make_request(
            types.RPCMethod("sendTransaction"),
            txn,
            {
                self._skip_preflight_key: opts.skip_preflight,
                self._preflight_comm_key: opts.preflight_commitment,
                self._encoding_key: "base64",
            },
        )
        print(f"{time.time()} request sent", flush=True)

        return self.__post_send(resp, opts.skip_confirmation, opts.preflight_commitment)

    def __post_send(self, resp: types.RPCResponse, skip_confirm: bool, conf_comm: Commitment) -> types.RPCResponse:
        if resp.get("error"):
            self._provider.logger.error(resp.get("error"))
        if not resp.get("result"):
            raise Exception("Failed to send transaction")
        if skip_confirm:
            return resp

        self._provider.logger.info(
            "Transaction sent to %s. Signature %s: ", self._provider.endpoint_uri, resp["result"]
        )

        return self.__confirm_transaction(resp["result"], conf_comm)

    def __confirm_transaction(self, tx_sig: str, commitment: Commitment = Max) -> types.RPCResponse:
        # TODO: This is incredibly hacky and needs to be cleaned up post-hackathon, use websockets...

        TIMEOUT = time.time() + 30  # 30 seconds  pylint: disable=invalid-name
        while time.time() < TIMEOUT:
            sig_status = self.get_signature_statuses([tx_sig])
            print(f"{sig_status=}", flush=True)
            if sig_status["result"]["value"][0] and \
                    sig_status["result"]["value"][0]["confirmationStatus"] in {commitment, "finalized"}:
                return sig_status
            print(f"sig_status: {sig_status}", flush=True)
            # if resp["result"]:
            #     break
            time.sleep(0.1)

        return None


class Wallet(ABC):
    def __init__(self, account: Account):
        self.account = account

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
        return self.account.public_key()

    def sign_transaction(self, tx: Transaction) -> Transaction:
        tx.sign(self.account)
        return tx

    def sign_all_transactions(self, txs: List[Transaction]):
        for tx in txs:
            tx.sign_partial(self.account)
        return txs

    @staticmethod
    def local() -> NodeWallet:
        fpath = os.path.expanduser("~/.config/solana/id.json")
        with open(fpath) as f:
            keypair = json.loads(f.read())
        return NodeWallet(Account(keypair[:32]))

    @staticmethod
    def random() -> NodeWallet:
        return NodeWallet(Account())

    @staticmethod
    def from_account(acc: Account):
        return NodeWallet(acc)
