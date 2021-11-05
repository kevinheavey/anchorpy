"""This module contains the invoke function."""
from typing import Optional
from solana.transaction import (
    AccountMeta,
    Transaction,
    TransactionInstruction,
    TransactionSignature,
)
from anchorpy.program.common import AddressType, translate_address
from anchorpy.provider import Provider


async def invoke(
    program_id: AddressType,
    provider: Provider,
    accounts: Optional[list[AccountMeta]] = None,
    data: Optional[bytes] = None,
) -> TransactionSignature:
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
