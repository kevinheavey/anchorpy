from __future__ import annotations
from typing import Dict, Union, List, Optional, cast
from enum import IntEnum
from solana.rpc.types import RPCError


class ExtendedRPCError(RPCError):
    data: dict
    logs: List[str]


class LangErrorCode(IntEnum):
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
    LangErrorCode.InstructionMissing: "8 byte instruction identifier not provided",
    LangErrorCode.InstructionFallbackNotFound: "Fallback functions are not supported",
    LangErrorCode.InstructionDidNotDeserialize: (
        "The program could not deserialize the given instruction"
    ),
    LangErrorCode.InstructionDidNotSerialize: (
        "The program could not serialize the given instruction"
    ),
    # Idl instructions.
    LangErrorCode.IdlInstructionStub: (
        "The program was compiled without idl instructions"
    ),
    LangErrorCode.IdlInstructionInvalidProgram: (
        "The transaction was given an invalid program for the IDL instruction"
    ),
    # Constraints.
    LangErrorCode.ConstraintMut: "A mut constraint was violated",
    LangErrorCode.ConstraintHasOne: "A has_one constraint was violated",
    LangErrorCode.ConstraintSigner: "A signer constraint was violated",
    LangErrorCode.ConstraintRaw: "A raw constraint was violated",
    LangErrorCode.ConstraintOwner: "An owner constraint was violated",
    LangErrorCode.ConstraintRentExempt: "A rent exempt constraint was violated",
    LangErrorCode.ConstraintSeeds: "A seeds constraint was violated",
    LangErrorCode.ConstraintExecutable: "An executable constraint was violated",
    LangErrorCode.ConstraintState: "A state constraint was violated",
    LangErrorCode.ConstraintAssociated: "An associated constraint was violated",
    LangErrorCode.ConstraintAssociatedInit: (
        "An associated init constraint was violated"
    ),
    LangErrorCode.ConstraintClose: "A close constraint was violated",
    LangErrorCode.ConstraintAddress: "An address constraint was violated",
    # Accounts.
    LangErrorCode.AccountDiscriminatorAlreadySet: (
        "The account discriminator was already set on this account"
    ),
    LangErrorCode.AccountDiscriminatorNotFound: (
        "No 8 byte discriminator was found on the account"
    ),
    LangErrorCode.AccountDiscriminatorMismatch: (
        "8 byte discriminator did not match what was expected"
    ),
    LangErrorCode.AccountDidNotDeserialize: "Failed to deserialize the account",
    LangErrorCode.AccountDidNotSerialize: "Failed to serialize the account",
    LangErrorCode.AccountNotEnoughKeys: (
        "Not enough account keys given to the instruction"
    ),
    LangErrorCode.AccountNotMutable: "The given account is not mutable",
    LangErrorCode.AccountNotProgramOwned: (
        "The given account is not owned by the executing program"
    ),
    LangErrorCode.InvalidProgramId: "Program ID was not as expected",
    LangErrorCode.InvalidProgramIdExecutable: "Program account is not executable",
    # State.
    LangErrorCode.StateInvalidAddress: (
        "The given state account does not have the correct address"
    ),
    # Misc.
    LangErrorCode.Deprecated: (
        "The API being used is deprecated and should no longer be used"
    ),
}


class ProgramError(Exception):
    """An error from a user defined program."""

    def __init__(self, code: int, msg: str) -> None:
        self.code = code
        self.msg = msg
        super().__init__(f"{code}: {msg}")

    @classmethod
    def parse(
        cls, err_info: Union[RPCError, ExtendedRPCError], idl_errors: Dict[int, str]
    ) -> Optional[ProgramError]:
        try:  # noqa: WPS229
            err_data = cast(ExtendedRPCError, err_info)["data"]
            custom_err_code = err_data["err"]["InstructionError"][1]["Custom"]
        except KeyError:
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
