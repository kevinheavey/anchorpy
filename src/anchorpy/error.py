"""This module handles AnchorPy errors."""
from __future__ import annotations
from typing import Union, Optional, cast
from enum import IntEnum
from solana.rpc.types import RPCError


class _ExtendedRPCError(RPCError):
    """RPCError with extra fields."""

    data: dict
    logs: list[str]


class AccountDoesNotExistError(Exception):
    """Raise if account doesn't exist."""


class AccountInvalidDiscriminator(Exception):
    """Raise if account discriminator doesn't match the IDL."""


class IdlNotFoundError(Exception):
    """Raise when requested IDL account does not exist."""


class ArgsError(Exception):
    """Raise when the incorrect number of args is passed to the RPC function."""


class _LangErrorCode(IntEnum):
    """Enumerates Anchor error codes."""

    # Instructions.
    InstructionMissing = 100
    InstructionFallbackNotFound = 101
    InstructionDidNotDeserialize = 102
    InstructionDidNotSerialize = 103
    # IDL instructions.
    IdlInstructionStub = 1000
    IdlInstructionInvalidProgram = 1001
    # Constraints.
    ConstraintMut = 2000
    ConstraintHasOne = 2001
    ConstraintSigner = 2002
    ConstraintRaw = 2003
    ConstraintOwner = 2004
    ConstraintRentExempt = 2005
    ConstraintSeeds = 2006
    ConstraintExecutable = 2007
    ConstraintState = 2008
    ConstraintAssociated = 2009
    ConstraintAssociatedInit = 2010
    ConstraintClose = 2011
    ConstraintAddress = 2012
    ConstraintZero = 2013
    ConstraintTokenMint = 2014
    ConstraintTokenOwner = 2015
    ConstraintMintMintAuthority = 2016
    ConstraintMintFreezeAuthority = 2017
    ConstraintMintDecimals = 2018
    ConstraintSpace = 2019
    # Require
    RequireViolated = 2500
    RequireEqViolated = 2501
    RequireKeysEqViolated = 2502
    RequireNeqViolated = 2503
    RequireKeysNeqViolated = 2504
    RequireGtViolated = 2505
    RequireGteViolated = 2506
    # Accounts.
    AccountDiscriminatorAlreadySet = 3000
    AccountDiscriminatorNotFound = 3001
    AccountDiscriminatorMismatch = 3002
    AccountDidNotDeserialize = 3003
    AccountDidNotSerialize = 3004
    AccountNotEnoughKeys = 3005
    AccountNotMutable = 3006
    AccountOwnedByWrongProgram = 3007
    InvalidProgramId = 3008
    InvalidProgramExecutable = 3009
    AccountNotSigner = 3010
    AccountNotSystemOwned = 3011
    AccountNotInitialized = 3012
    AccountNotProgramData = 3013
    AccountNotAssociatedTokenAccount = 3014
    AccountSysvarMismatch = 3015
    # State.
    StateInvalidAddress = 4000

    # Used for APIs that shouldn't be used anymore.
    Deprecated = 5000


LangErrorMessage = {
    # Instructions.
    _LangErrorCode.InstructionMissing: "8 byte instruction identifier not provided",
    _LangErrorCode.InstructionFallbackNotFound: "Fallback functions are not supported",
    _LangErrorCode.InstructionDidNotDeserialize: (
        "The program could not deserialize the given instruction"
    ),
    _LangErrorCode.InstructionDidNotSerialize: (
        "The program could not serialize the given instruction"
    ),
    # Idl instructions.
    _LangErrorCode.IdlInstructionStub: (
        "The program was compiled without idl instructions"
    ),
    _LangErrorCode.IdlInstructionInvalidProgram: (
        "The transaction was given an invalid program for the IDL instruction"
    ),
    # Constraints.
    _LangErrorCode.ConstraintMut: "A mut constraint was violated",
    _LangErrorCode.ConstraintHasOne: "A has_one constraint was violated",
    _LangErrorCode.ConstraintSigner: "A signer constraint was violated",
    _LangErrorCode.ConstraintRaw: "A raw constraint was violated",
    _LangErrorCode.ConstraintOwner: "An owner constraint was violated",
    _LangErrorCode.ConstraintRentExempt: "A rent exempt constraint was violated",
    _LangErrorCode.ConstraintSeeds: "A seeds constraint was violated",
    _LangErrorCode.ConstraintExecutable: "An executable constraint was violated",
    _LangErrorCode.ConstraintState: "A state constraint was violated",
    _LangErrorCode.ConstraintAssociated: "An associated constraint was violated",
    _LangErrorCode.ConstraintAssociatedInit: (
        "An associated init constraint was violated"
    ),
    _LangErrorCode.ConstraintClose: "A close constraint was violated",
    _LangErrorCode.ConstraintAddress: "An address constraint was violated",
    _LangErrorCode.ConstraintZero: "Expected zero account discriminant",
    _LangErrorCode.ConstraintTokenMint: "A token mint constraint was violated",
    _LangErrorCode.ConstraintTokenOwner: "A token owner constraint was violated",
    _LangErrorCode.ConstraintMintMintAuthority: (
        "A mint mint authority constraint was violated"
    ),
    _LangErrorCode.ConstraintMintFreezeAuthority: (
        "A mint freeze authority constraint was violated"
    ),
    _LangErrorCode.ConstraintMintDecimals: "A mint decimals constraint was violated",
    _LangErrorCode.ConstraintSpace: "A space constraint was violated",
    # Require.
    _LangErrorCode.RequireViolated: "A require expression was violated",
    _LangErrorCode.RequireEqViolated: "A require_eq expression was violated",
    _LangErrorCode.RequireKeysEqViolated: "A require_keys_eq expression was violated",
    _LangErrorCode.RequireNeqViolated: "A require_neq expression was violated",
    _LangErrorCode.RequireKeysNeqViolated: "A require_keys_neq expression was violated",
    _LangErrorCode.RequireGtViolated: "A require_gt expression was violated",
    _LangErrorCode.RequireGteViolated: "A require_gte expression was violated",
    # Accounts.
    _LangErrorCode.AccountDiscriminatorAlreadySet: (
        "The account discriminator was already set on this account"
    ),
    _LangErrorCode.AccountDiscriminatorNotFound: (
        "No 8 byte discriminator was found on the account"
    ),
    _LangErrorCode.AccountDiscriminatorMismatch: (
        "8 byte discriminator did not match what was expected"
    ),
    _LangErrorCode.AccountDidNotDeserialize: "Failed to deserialize the account",
    _LangErrorCode.AccountDidNotSerialize: "Failed to serialize the account",
    _LangErrorCode.AccountNotEnoughKeys: (
        "Not enough account keys given to the instruction"
    ),
    _LangErrorCode.AccountNotMutable: "The given account is not mutable",
    _LangErrorCode.AccountOwnedByWrongProgram: (
        "The given account is owned by a different program than expected"
    ),
    _LangErrorCode.InvalidProgramId: "Program ID was not as expected",
    _LangErrorCode.InvalidProgramExecutable: "Program account is not executable",
    _LangErrorCode.AccountNotSigner: "The given account did not sign",
    _LangErrorCode.AccountNotSystemOwned: (
        "The given account is not owned by the system program"
    ),
    _LangErrorCode.AccountNotInitialized: (
        "The program expected this account to be already initialized"
    ),
    _LangErrorCode.AccountNotProgramData: (
        "The given account is not a program data account"
    ),
    _LangErrorCode.AccountNotAssociatedTokenAccount: (
        "The given account is not the associated token account"
    ),
    _LangErrorCode.AccountSysvarMismatch: (
        "The given public key does not match the required sysvar"
    ),
    # State.
    _LangErrorCode.StateInvalidAddress: (
        "The given state account does not have the correct address"
    ),
    # Misc.
    _LangErrorCode.Deprecated: (
        "The API being used is deprecated and should no longer be used"
    ),
}


class ProgramError(Exception):
    """An error from a user defined program."""

    def __init__(
        self, code: int, msg: Optional[str], logs: Optional[list[str]] = None
    ) -> None:
        """Init.

        Args:
            code: The error code.
            msg: The error message.
            logs: The transaction simulation logs.
        """
        self.code = code
        self.msg = msg
        self.logs = logs
        super().__init__(f"{code}: {msg}")

    @classmethod
    def parse(
        cls,
        err_info: Union[RPCError, _ExtendedRPCError],
        idl_errors: dict[int, str],
    ) -> Optional[ProgramError]:
        """Convert an RPC error into a ProgramError, if possible.

        Args:
            err_info: The plain RPC error.
            idl_errors: Errors from the IDL file.

        Returns:
            A ProgramError or None.
        """
        try:  # noqa: WPS229
            err_data = cast(_ExtendedRPCError, err_info)["data"]
            custom_err_code = err_data["err"]["InstructionError"][1]["Custom"]
            logs = cast(Optional[list[str]], err_data.get("logs"))
        except (KeyError, TypeError):
            return None
        # parse user error
        msg = idl_errors.get(custom_err_code)
        if msg is not None:
            return cls(custom_err_code, msg, logs)
        # parse framework internal error
        msg = LangErrorMessage.get(custom_err_code)
        if msg is not None:
            return cls(custom_err_code, msg, logs)
        # Unable to parse the error. Just return the untranslated error.
        return None
