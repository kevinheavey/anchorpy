"""Solana RPC and token types across the NamedTuple-to-model transition."""
from typing import NamedTuple, Optional

from solders.pubkey import Pubkey

__all__ = [
    "AccountInfo",
    "InitializeAccountParams",
    "InitializeMintParams",
    "MintInfo",
    "MintToParams",
    "rpc_types",
]

try:
    import solana.rpc.models as rpc_types  # type: ignore[import]
except ModuleNotFoundError as exc:
    if exc.name != "solana.rpc.models":
        raise
    import solana.rpc.types as rpc_types  # type: ignore[no-redef]

try:
    from spl.token.models import (  # type: ignore[import]
        InitializeAccountParams,
        InitializeMintParams,
        MintToParams,
    )
except ModuleNotFoundError as exc:
    if exc.name != "spl.token.models":
        raise
    from spl.token.instructions import (
        InitializeAccountParams,
        InitializeMintParams,
        MintToParams,
    )

try:
    from spl.token.core import AccountInfo, MintInfo
except ModuleNotFoundError as exc:
    if exc.name != "spl.token.core":
        raise

    # Keep the tuple contract of AnchorPy's parse_token_account/parse_mint_account
    # helpers after solana-py removes its original NamedTuple definitions.
    class AccountInfo(NamedTuple):  # type: ignore[no-redef]
        mint: Pubkey
        owner: Pubkey
        amount: int
        delegate: Optional[Pubkey]
        delegated_amount: int
        is_initialized: bool
        is_frozen: bool
        is_native: bool
        rent_exempt_reserve: Optional[int]
        close_authority: Optional[Pubkey]

    class MintInfo(NamedTuple):  # type: ignore[no-redef]
        mint_authority: Optional[Pubkey]
        supply: int
        decimals: int
        is_initialized: bool
        freeze_authority: Optional[Pubkey]
