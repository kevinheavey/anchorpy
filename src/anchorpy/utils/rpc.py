"""This module contains the invoke function."""
from dataclasses import dataclass
from base64 import b64decode
from asyncio import gather
from typing import Any, Optional, NamedTuple
from solana.rpc.core import RPCException
from toolz import partition_all, concat
from solders.signature import Signature
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solana.transaction import (
    AccountMeta,
    Transaction,
    TransactionInstruction,
)
import zstandard
import jsonrpcclient
from anchorpy.program.common import AddressType, translate_address
from anchorpy.provider import Provider

_GET_MULTIPLE_ACCOUNTS_LIMIT = 100
_MAX_ACCOUNT_SIZE = 10 * 1048576


class AccountInfo(NamedTuple):
    """Information describing an account.

    Attributes:
        executable: `True` if this account's data contains a loaded program.
        owner: Identifier of the program that owns the account.
        lamports: Number of lamports assigned to the account.
        data: Optional data assigned to the account.
        rent_epoch: Optional rent epoch info for for account.
    """

    executable: bool
    owner: PublicKey
    lamports: int
    data: bytes
    rent_epoch: Optional[int]


async def invoke(
    program_id: AddressType,
    provider: Provider,
    accounts: Optional[list[AccountMeta]] = None,
    data: Optional[bytes] = None,
) -> Signature:
    """Send a transaction to a program with the given accounts and instruction data.

    Args:
        program_id: The program ID
        provider: the `Provider` instance.
        accounts: `AccountMeta` objects.
        data: The transaction data.

    Returns:
        The transaction signature.
    """
    translated_program_id = translate_address(program_id)
    tx = Transaction()
    tx.add(
        TransactionInstruction(
            program_id=translated_program_id,
            keys=[] if accounts is None else accounts,
            data=bytes(0) if data is None else data,
        ),
    )
    return await provider.send(tx)


@dataclass
class _MultipleAccountsItem:
    pubkey: PublicKey
    account: AccountInfo


async def get_multiple_accounts(
    connection: AsyncClient,
    pubkeys: list[PublicKey],
    batch_size: int = 3,
    commitment: Optional[Commitment] = None,
) -> list[Optional[_MultipleAccountsItem]]:
    """Fetch multiple account infos through batched `getMultipleAccount` RPC requests.

    Args:
        connection: The `solana-py` client object.
        pubkeys: Pubkeys to fetch.
        batch_size: The number of `getMultipleAccount` objects to include in each
            HTTP request.
        commitment: Bank state to query.

    Returns:
        Account infos and pubkeys.
    """
    pubkeys_per_network_request = _GET_MULTIPLE_ACCOUNTS_LIMIT * batch_size
    chunks = partition_all(pubkeys_per_network_request, pubkeys)
    awaitables = [
        _get_multiple_accounts_core(connection, pubkeys_chunk, commitment)
        for pubkeys_chunk in chunks
    ]
    results = await gather(*awaitables, return_exceptions=False)
    return list(concat(results))


async def _get_multiple_accounts_core(
    connection: AsyncClient, pubkeys: list[PublicKey], commitment: Optional[Commitment]
) -> list[Optional[_MultipleAccountsItem]]:
    pubkey_batches = partition_all(_GET_MULTIPLE_ACCOUNTS_LIMIT, pubkeys)
    rpc_requests: list[dict[str, Any]] = []
    commitment_to_use = connection._commitment if commitment is None else commitment
    for pubkey_batch in pubkey_batches:
        pubkeys_to_send = [str(pubkey) for pubkey in pubkey_batch]
        rpc_request = jsonrpcclient.request(
            "getMultipleAccounts",
            params=[
                pubkeys_to_send,
                {"encoding": "base64+zstd", "commitment": commitment_to_use},
            ],
        )
        rpc_requests.append(rpc_request)
    resp = await connection._provider.session.post(
        connection._provider.endpoint_uri,
        json=rpc_requests,
        headers={"content-encoding": "gzip"},
    )
    parsed = jsonrpcclient.parse(resp.json())
    result: list[Optional[_MultipleAccountsItem]] = []
    dctx = zstandard.ZstdDecompressor()
    idx = 0
    for rpc_result in parsed:
        if isinstance(rpc_result, jsonrpcclient.Error):
            raise RPCException(
                f"Failed to get info about accounts: {rpc_result.message}"
            )
        for account in rpc_result.result["value"]:
            if account is None:
                result.append(None)
            else:
                acc_info_data = account["data"][0]
                decoded = b64decode(acc_info_data)
                decompressed = dctx.decompress(
                    decoded, max_output_size=_MAX_ACCOUNT_SIZE
                )
                acc_info = AccountInfo(
                    executable=account["executable"],
                    owner=PublicKey(account["owner"]),
                    lamports=account["lamports"],
                    data=decompressed,
                    rent_epoch=account["rentEpoch"],
                )
                multiple_accounts_item = _MultipleAccountsItem(
                    pubkey=pubkeys[idx], account=acc_info
                )
                result.append(multiple_accounts_item)
            idx += 1
    return result
