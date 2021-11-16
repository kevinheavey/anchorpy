from typing import Optional
from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.rpc.types import RPCResponse
from solana.transaction import Transaction
from solana.system_program import create_account, CreateAccountParams
from solana.utils.helpers import decode_byte_string
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from spl.token.instructions import (
    initialize_mint,
    InitializeMintParams,
    initialize_account,
    InitializeAccountParams,
    mint_to,
    MintToParams,
)
from spl.token.core import AccountInfo, MintInfo
from spl.token._layouts import ACCOUNT_LAYOUT, MINT_LAYOUT
from anchorpy import Provider


def associated_address(mint: PublicKey, owner: PublicKey) -> PublicKey:
    return PublicKey.find_program_address(
        [bytes(owner), bytes(TOKEN_PROGRAM_ID), bytes(mint)],
        ASSOCIATED_TOKEN_PROGRAM_ID,
    )[0]


async def create_mint_and_vault(
    provider: Provider, amount: int, owner: Optional[PublicKey], decimals: Optional[int]
) -> tuple[PublicKey, PublicKey]:
    actual_owner = provider.wallet.public_key if owner is None else owner
    mint = Keypair()
    vault = Keypair()
    tx = Transaction()
    mint_space = 82
    create_mint_mbre_resp = (
        await provider.client.get_minimum_balance_for_rent_exemption(mint_space)
    )
    create_mint_mbre = create_mint_mbre_resp["result"]
    create_mint_account_params = CreateAccountParams(
        from_pubkey=provider.wallet.public_key,
        new_account_pubkey=mint.public_key,
        space=mint_space,
        lamports=create_mint_mbre,
        program_id=TOKEN_PROGRAM_ID,
    )
    create_mint_account_instruction = create_account(
        create_mint_account_params,
    )
    init_mint_instruction = initialize_mint(
        InitializeMintParams(
            mint=mint.public_key,
            decimals=0 if decimals is None else decimals,
            mint_authority=provider.wallet.public_key,
            program_id=TOKEN_PROGRAM_ID,
        ),
    )
    vault_space = 165
    create_vault_mbre_resp = (
        await provider.client.get_minimum_balance_for_rent_exemption(vault_space)
    )
    create_vault_mbre = create_vault_mbre_resp["result"]
    create_vault_account_instruction = create_account(
        CreateAccountParams(
            from_pubkey=provider.wallet.public_key,
            new_account_pubkey=vault.public_key,
            space=vault_space,
            lamports=create_vault_mbre,
            program_id=TOKEN_PROGRAM_ID,
        ),
    )
    init_vault_instruction = initialize_account(
        InitializeAccountParams(
            program_id=TOKEN_PROGRAM_ID,
            account=vault.public_key,
            mint=mint.public_key,
            owner=actual_owner,
        ),
    )
    mint_to_instruction = mint_to(
        MintToParams(
            program_id=TOKEN_PROGRAM_ID,
            mint=mint.public_key,
            dest=vault.public_key,
            amount=amount,
            mint_authority=provider.wallet.public_key,
        ),
    )
    tx.add(
        create_mint_account_instruction,
        init_mint_instruction,
        create_vault_account_instruction,
        init_vault_instruction,
        mint_to_instruction,
    )
    await provider.send(tx, [mint, vault])
    return mint.public_key, vault.public_key


def parse_token_account(info: RPCResponse) -> AccountInfo:
    if not info:
        raise ValueError("Invalid account owner")

    if info["result"]["value"]["owner"] != str(TOKEN_PROGRAM_ID):
        raise AttributeError("Invalid account owner")

    bytes_data = decode_byte_string(info["result"]["value"]["data"][0])
    if len(bytes_data) != ACCOUNT_LAYOUT.sizeof():
        raise ValueError("Invalid account size")

    decoded_data = ACCOUNT_LAYOUT.parse(bytes_data)

    mint = PublicKey(decoded_data.mint)
    owner = PublicKey(decoded_data.owner)
    amount = decoded_data.amount

    if decoded_data.delegate_option == 0:
        delegate = None
        delegated_amount = 0
    else:
        delegate = PublicKey(decoded_data.delegate)
        delegated_amount = decoded_data.delegated_amount

    is_initialized = decoded_data.state != 0
    is_frozen = decoded_data.state == 2

    if decoded_data.is_native_option == 1:
        rent_exempt_reserve = decoded_data.is_native
        is_native = True
    else:
        rent_exempt_reserve = None
        is_native = False

    if decoded_data.close_authority_option == 0:
        close_authority = None
    else:
        close_authority = PublicKey(decoded_data.owner)

    return AccountInfo(
        mint,
        owner,
        amount,
        delegate,
        delegated_amount,
        is_initialized,
        is_frozen,
        is_native,
        rent_exempt_reserve,
        close_authority,
    )


async def get_token_account(provider: Provider, addr: PublicKey) -> AccountInfo:
    depositor_acc_info_raw = await provider.client.get_account_info(addr)
    return parse_token_account(depositor_acc_info_raw)


async def get_mint_info(
    provider: Provider,
    addr: PublicKey,
) -> MintInfo:
    depositor_acc_info_raw = await provider.client.get_account_info(addr)
    return parse_mint_account(depositor_acc_info_raw)


def parse_mint_account(info: RPCResponse) -> MintInfo:
    owner = info["result"]["value"]["owner"]
    if owner != str(TOKEN_PROGRAM_ID):
        raise AttributeError(f"Invalid mint owner: {owner}")

    bytes_data = decode_byte_string(info["result"]["value"]["data"][0])
    if len(bytes_data) != MINT_LAYOUT.sizeof():
        raise ValueError("Invalid mint size")

    decoded_data = MINT_LAYOUT.parse(bytes_data)
    decimals = decoded_data.decimals

    if decoded_data.mint_authority_option == 0:
        mint_authority = None
    else:
        mint_authority = PublicKey(decoded_data.mint_authority)

    supply = decoded_data.supply
    is_initialized = decoded_data.is_initialized != 0

    if decoded_data.freeze_authority_option == 0:
        freeze_authority = None
    else:
        freeze_authority = PublicKey(decoded_data.freeze_authority)

    return MintInfo(mint_authority, supply, decimals, is_initialized, freeze_authority)
