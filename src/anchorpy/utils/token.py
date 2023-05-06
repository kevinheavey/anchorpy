"""This module contains utilities for the SPL Token Program."""
from typing import Optional

from solana.rpc.commitment import Confirmed
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.rpc.responses import GetAccountInfoResp
from solders.system_program import CreateAccountParams, create_account
from solders.transaction import VersionedTransaction
from spl.token._layouts import ACCOUNT_LAYOUT, MINT_LAYOUT
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.core import AccountInfo, MintInfo
from spl.token.instructions import (
    InitializeAccountParams,
    InitializeMintParams,
    MintToParams,
    initialize_account,
    initialize_mint,
    mint_to,
)

from anchorpy.provider import Provider


async def create_token_account(
    prov: Provider,
    mint: Pubkey,
    owner: Pubkey,
) -> Pubkey:
    """Create a token account.

    Args:
        prov: An anchorpy Provider instance.
        mint: The pubkey of the token's mint.
        owner: User account that will own the new account.

    Returns:
        The pubkey of the new account.
    """
    token = AsyncToken(prov.connection, mint, TOKEN_PROGRAM_ID, prov.wallet.payer)
    return await token.create_account(owner)


async def create_token_account_instrs(
    provider: Provider,
    new_account_pubkey: Pubkey,
    mint: Pubkey,
    owner: Pubkey,
) -> tuple[Instruction, Instruction]:
    """Generate instructions for creating a token account.

    Args:
        provider: An anchorpy Provider instance.
        new_account_pubkey: The pubkey of the new account.
        mint: The pubkey of the token's mint.
        owner: User account that will own the new account.

    Returns:
        Transaction instructions to create the new account.
    """
    mbre_resp = await provider.connection.get_minimum_balance_for_rent_exemption(165)
    lamports = mbre_resp.value
    return (
        create_account(
            CreateAccountParams(
                from_pubkey=provider.wallet.public_key,
                to_pubkey=new_account_pubkey,
                space=165,
                lamports=lamports,
                owner=TOKEN_PROGRAM_ID,
            )
        ),
        initialize_account(
            InitializeAccountParams(
                account=new_account_pubkey,
                mint=mint,
                owner=owner,
                program_id=TOKEN_PROGRAM_ID,
            )
        ),
    )


async def create_mint_and_vault(
    provider: Provider,
    amount: int,
    owner: Optional[Pubkey] = None,
    decimals: Optional[int] = None,
) -> tuple[Pubkey, Pubkey]:
    """Create a mint and a vault, then mint tokens to the vault.

    Args:
        provider: An anchorpy Provider instance.
        amount: The amount of tokens to mint to the vault.
        owner: User account that will own the new account.
        decimals: The number of decimal places for the token to support.

    Returns:
        The mint and vault pubkeys.
    """
    actual_owner = provider.wallet.public_key if owner is None else owner
    mint = Keypair()
    vault = Keypair()
    mint_space = 82
    create_mint_mbre_resp = (
        await provider.connection.get_minimum_balance_for_rent_exemption(mint_space)
    )
    create_mint_mbre = create_mint_mbre_resp.value
    create_mint_account_params = CreateAccountParams(
        from_pubkey=provider.wallet.public_key,
        to_pubkey=mint.pubkey(),
        space=mint_space,
        lamports=create_mint_mbre,
        owner=TOKEN_PROGRAM_ID,
    )
    create_mint_account_instruction = create_account(
        create_mint_account_params,
    )
    init_mint_instruction = initialize_mint(
        InitializeMintParams(
            mint=mint.pubkey(),
            decimals=0 if decimals is None else decimals,
            mint_authority=provider.wallet.public_key,
            program_id=TOKEN_PROGRAM_ID,
        ),
    )
    vault_space = 165
    create_vault_mbre_resp = (
        await provider.connection.get_minimum_balance_for_rent_exemption(vault_space)
    )
    create_vault_mbre = create_vault_mbre_resp.value
    create_vault_account_instruction = create_account(
        CreateAccountParams(
            from_pubkey=provider.wallet.public_key,
            to_pubkey=vault.pubkey(),
            space=vault_space,
            lamports=create_vault_mbre,
            owner=TOKEN_PROGRAM_ID,
        ),
    )
    init_vault_instruction = initialize_account(
        InitializeAccountParams(
            program_id=TOKEN_PROGRAM_ID,
            account=vault.pubkey(),
            mint=mint.pubkey(),
            owner=actual_owner,
        ),
    )
    mint_to_instruction = mint_to(
        MintToParams(
            program_id=TOKEN_PROGRAM_ID,
            mint=mint.pubkey(),
            dest=vault.pubkey(),
            amount=amount,
            mint_authority=provider.wallet.public_key,
        ),
    )
    blockhash = (
        await provider.connection.get_latest_blockhash(Confirmed)
    ).value.blockhash
    msg = Message.new_with_blockhash(
        [
            create_mint_account_instruction,
            init_mint_instruction,
            create_vault_account_instruction,
            init_vault_instruction,
            mint_to_instruction,
        ],
        provider.wallet.public_key,
        blockhash,
    )
    tx = VersionedTransaction(msg, [provider.wallet.payer, mint, vault])
    await provider.send(tx)
    return mint.pubkey(), vault.pubkey()


def parse_token_account(info: GetAccountInfoResp) -> AccountInfo:
    """Parse `AccountInfo` from RPC response.

    Args:
        info: the `get_account_info` RPC response.

    Raises:
        ValueError: If the fetched data is the wrong size.
        AttributeError: If the account is not owned by the token program.

    Returns:
        The parsed `AccountInfo`.
    """
    val = info.value
    if not val:
        raise ValueError("Invalid account owner")

    if val.owner != TOKEN_PROGRAM_ID:
        raise AttributeError("Invalid account owner")

    bytes_data = val.data
    if len(bytes_data) != ACCOUNT_LAYOUT.sizeof():
        raise ValueError("Invalid account size")

    decoded_data = ACCOUNT_LAYOUT.parse(bytes_data)

    mint = Pubkey(decoded_data.mint)
    owner = Pubkey(decoded_data.owner)
    amount = decoded_data.amount

    if decoded_data.delegate_option == 0:
        delegate = None
        delegated_amount = 0
    else:
        delegate = Pubkey(decoded_data.delegate)
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
        close_authority = Pubkey(decoded_data.owner)

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


async def get_token_account(provider: Provider, addr: Pubkey) -> AccountInfo:
    """Retrieve token account information.

    Args:
        provider: The anchorpy Provider instance.
        addr: The pubkey of the token account.

    Returns:
        The parsed `AccountInfo` of the token account.
    """
    depositor_acc_info_raw = await provider.connection.get_account_info(addr)
    return parse_token_account(depositor_acc_info_raw)


async def get_mint_info(
    provider: Provider,
    addr: Pubkey,
) -> MintInfo:
    """Retrieve mint information.

    Args:
        provider: The anchorpy Provider instance.
        addr: The pubkey of the mint.

    Returns:
        The parsed `MintInfo`.
    """
    depositor_acc_info_raw = await provider.connection.get_account_info(addr)
    return parse_mint_account(depositor_acc_info_raw)


def parse_mint_account(info: GetAccountInfoResp) -> MintInfo:
    """Parse raw RPC response into `MintInfo`.

    Args:
        info: The RPC response from calling `.get_account_info` for the mint pubkey.

    Raises:
        AttributeError: If the account is not owned by the Token Program.
        ValueError: If the fetched data is the wrong size.

    Returns:
        The parsed `MintInfo`.
    """
    val = info.value
    if val is None:
        raise ValueError("Account does not exist.")
    owner = val.owner
    if owner != TOKEN_PROGRAM_ID:
        raise AttributeError(f"Invalid mint owner: {owner}")

    bytes_data = val.data
    if len(bytes_data) != MINT_LAYOUT.sizeof():
        raise ValueError("Invalid mint size")

    decoded_data = MINT_LAYOUT.parse(bytes_data)
    decimals = decoded_data.decimals

    mint_authority = (
        None
        if decoded_data.mint_authority_option == 0
        else Pubkey(decoded_data.mint_authority)
    )

    supply = decoded_data.supply
    is_initialized = decoded_data.is_initialized != 0

    if decoded_data.freeze_authority_option == 0:
        freeze_authority = None
    else:
        freeze_authority = Pubkey(decoded_data.freeze_authority)

    return MintInfo(mint_authority, supply, decimals, is_initialized, freeze_authority)
