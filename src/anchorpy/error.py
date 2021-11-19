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
    IdlInstructionStub = 120
    IdlInstructionInvalidProgram = 121
    # Constraints.
    ConstraintMut = 140
    ConstraintHasOne = 141
    ConstraintSigner = 142
    ConstraintRaw = 143
    ConstraintOwner = 144
    ConstraintRentExempt = 145
    ConstraintSeeds = 146
    ConstraintExecutable = 147
    ConstraintState = 148
    ConstraintAssociated = 149
    ConstraintAssociatedInit = 150
    ConstraintClose = 151
    ConstraintAddress = 152
    # Accounts.
    AccountDiscriminatorAlreadySet = 160
    AccountDiscriminatorNotFound = 161
    AccountDiscriminatorMismatch = 162
    AccountDidNotDeserialize = 163
    AccountDidNotSerialize = 164
    AccountNotEnoughKeys = 165
    AccountNotMutable = 166
    AccountNotProgramOwned = 167
    InvalidProgramId = 168
    InvalidProgramIdExecutable = 169
    # State.
    StateInvalidAddress = 180
    # Used for APIs that shouldn't be used anymore.
    Deprecated = 299


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
    _LangErrorCode.AccountNotProgramOwned: (
        "The given account is not owned by the executing program"
    ),
    _LangErrorCode.InvalidProgramId: "Program ID was not as expected",
    _LangErrorCode.InvalidProgramIdExecutable: "Program account is not executable",
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

    def __init__(self, code: int, msg: str) -> None:
        """Init.

        Args:
            code: The error code.
            msg: The error message.
        """
        self.code = code
        self.msg = msg
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
        except (KeyError, TypeError):
            return None
        # parse user error
        msg = idl_errors.get(custom_err_code)
        if msg is not None:
            return ProgramError(custom_err_code, msg)
        # parse framework internal error
        msg = LangErrorMessage.get(custom_err_code)
        if msg is not None:
            return ProgramError(custom_err_code, msg)
        # Unable to parse the error. Just return the untranslated error.
        return None
