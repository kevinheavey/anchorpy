"""This module contains the invoke function."""
from asyncio import gather
from dataclasses import dataclass
from typing import NamedTuple, Optional, Union, cast

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment, Confirmed, Finalized, Processed
from solana.rpc.core import RPCException
from solana.transaction import Transaction
from solders.account import Account
from solders.account_decoder import UiAccountEncoding
from solders.commitment_config import CommitmentLevel
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey
from solders.rpc.config import RpcAccountInfoConfig
from solders.rpc.requests import GetMultipleAccounts, batch_to_json
from solders.rpc.responses import GetMultipleAccountsResp, RPCError, batch_from_json
from solders.signature import Signature
from toolz import concat, partition_all

from anchorpy.program.common import AddressType, translate_address
from anchorpy.provider import Provider

_GET_MULTIPLE_ACCOUNTS_LIMIT = 100
_MAX_ACCOUNT_SIZE = 10 * 1048576

_COMMITMENT_TO_SOLDERS = {
    Finalized: CommitmentLevel.Finalized,
    Confirmed: CommitmentLevel.Confirmed,
    Processed: CommitmentLevel.Processed,
}


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
    owner: Pubkey
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
        Instruction(
            program_id=translated_program_id,
            accounts=[] if accounts is None else accounts,
            data=bytes(0) if data is None else data,
        ),
    )
    return await provider.send(tx)


@dataclass
class _MultipleAccountsItem:
    pubkey: Pubkey
    account: Account


async def get_multiple_accounts(
    connection: AsyncClient,
    pubkeys: list[Pubkey],
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
    connection: AsyncClient, pubkeys: list[Pubkey], commitment: Optional[Commitment]
) -> list[Optional[_MultipleAccountsItem]]:
    pubkey_batches = partition_all(_GET_MULTIPLE_ACCOUNTS_LIMIT, pubkeys)
    rpc_requests: list[GetMultipleAccounts] = []
    commitment_to_use = connection._commitment if commitment is None else commitment
    for pubkey_batch in pubkey_batches:
        rpc_req = GetMultipleAccounts(
            list(pubkey_batch),
            RpcAccountInfoConfig(
                encoding=UiAccountEncoding.Base64Zstd,
                commitment=_COMMITMENT_TO_SOLDERS[commitment_to_use],
            ),
        )
        rpc_requests.append(rpc_req)
    resp = await connection._provider.session.post(
        connection._provider.endpoint_uri,
        content=batch_to_json(rpc_requests),
        headers={"content-encoding": "gzip", "Content-type": "application/json"},
    )
    parsed = cast(
        list[Union[RPCError, GetMultipleAccountsResp]],
        batch_from_json(resp.text, [GetMultipleAccountsResp for _ in rpc_requests]),
    )
    result: list[Optional[_MultipleAccountsItem]] = []
    idx = 0
    for rpc_result in parsed:
        if not isinstance(rpc_result, GetMultipleAccountsResp):
            raise RPCException(f"Failed to get info about accounts: {rpc_result}")
        for account in rpc_result.value:
            if account is None:
                result.append(None)
            else:
                multiple_accounts_item = _MultipleAccountsItem(
                    pubkey=pubkeys[idx], account=account
                )
                result.append(multiple_accounts_item)
            idx += 1
    return result
