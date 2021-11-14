from typing import Optional
from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.transaction import Transaction
from solana.system_program import create_account, CreateAccountParams
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from spl.token.instructions import (
    initialize_mint,
    InitializeMintParams,
    initialize_account,
    InitializeAccountParams,
    mint_to,
    MintToParams,
)
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
