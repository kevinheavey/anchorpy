import typing
from anchorpy.error import ProgramError


class NotRentExempt(ProgramError):
    def __init__(self) -> None:
        super().__init__(0, "Lamport balance below rent-exempt threshold")

    code = 0
    name = "NotRentExempt"
    msg = "Lamport balance below rent-exempt threshold"


class InsufficientFunds(ProgramError):
    def __init__(self) -> None:
        super().__init__(1, "Insufficient funds")

    code = 1
    name = "InsufficientFunds"
    msg = "Insufficient funds"


class InvalidMint(ProgramError):
    def __init__(self) -> None:
        super().__init__(2, "Invalid Mint")

    code = 2
    name = "InvalidMint"
    msg = "Invalid Mint"


class MintMismatch(ProgramError):
    def __init__(self) -> None:
        super().__init__(3, "Account not associated with this Mint")

    code = 3
    name = "MintMismatch"
    msg = "Account not associated with this Mint"


class OwnerMismatch(ProgramError):
    def __init__(self) -> None:
        super().__init__(4, "Owner does not match")

    code = 4
    name = "OwnerMismatch"
    msg = "Owner does not match"


class FixedSupply(ProgramError):
    def __init__(self) -> None:
        super().__init__(5, "Fixed supply")

    code = 5
    name = "FixedSupply"
    msg = "Fixed supply"


class AlreadyInUse(ProgramError):
    def __init__(self) -> None:
        super().__init__(6, "Already in use")

    code = 6
    name = "AlreadyInUse"
    msg = "Already in use"


class InvalidNumberOfProvidedSigners(ProgramError):
    def __init__(self) -> None:
        super().__init__(7, "Invalid number of provided signers")

    code = 7
    name = "InvalidNumberOfProvidedSigners"
    msg = "Invalid number of provided signers"


class InvalidNumberOfRequiredSigners(ProgramError):
    def __init__(self) -> None:
        super().__init__(8, "Invalid number of required signers")

    code = 8
    name = "InvalidNumberOfRequiredSigners"
    msg = "Invalid number of required signers"


class UninitializedState(ProgramError):
    def __init__(self) -> None:
        super().__init__(9, "State is unititialized")

    code = 9
    name = "UninitializedState"
    msg = "State is unititialized"


class NativeNotSupported(ProgramError):
    def __init__(self) -> None:
        super().__init__(10, "Instruction does not support native tokens")

    code = 10
    name = "NativeNotSupported"
    msg = "Instruction does not support native tokens"


class NonNativeHasBalance(ProgramError):
    def __init__(self) -> None:
        super().__init__(
            11, "Non-native account can only be closed if its balance is zero"
        )

    code = 11
    name = "NonNativeHasBalance"
    msg = "Non-native account can only be closed if its balance is zero"


class InvalidInstruction(ProgramError):
    def __init__(self) -> None:
        super().__init__(12, "Invalid instruction")

    code = 12
    name = "InvalidInstruction"
    msg = "Invalid instruction"


class InvalidState(ProgramError):
    def __init__(self) -> None:
        super().__init__(13, "State is invalid for requested operation")

    code = 13
    name = "InvalidState"
    msg = "State is invalid for requested operation"


class Overflow(ProgramError):
    def __init__(self) -> None:
        super().__init__(14, "Operation overflowed")

    code = 14
    name = "Overflow"
    msg = "Operation overflowed"


class AuthorityTypeNotSupported(ProgramError):
    def __init__(self) -> None:
        super().__init__(15, "Account does not support specified authority type")

    code = 15
    name = "AuthorityTypeNotSupported"
    msg = "Account does not support specified authority type"


class MintCannotFreeze(ProgramError):
    def __init__(self) -> None:
        super().__init__(16, "This token mint cannot freeze accounts")

    code = 16
    name = "MintCannotFreeze"
    msg = "This token mint cannot freeze accounts"


class AccountFrozen(ProgramError):
    def __init__(self) -> None:
        super().__init__(17, "Account is frozen")

    code = 17
    name = "AccountFrozen"
    msg = "Account is frozen"


class MintDecimalsMismatch(ProgramError):
    def __init__(self) -> None:
        super().__init__(
            18, "The provided decimals value different from the Mint decimals"
        )

    code = 18
    name = "MintDecimalsMismatch"
    msg = "The provided decimals value different from the Mint decimals"


class NonNativeNotSupported(ProgramError):
    def __init__(self) -> None:
        super().__init__(19, "Instruction does not support non-native tokens")

    code = 19
    name = "NonNativeNotSupported"
    msg = "Instruction does not support non-native tokens"


CustomError = typing.Union[
    NotRentExempt,
    InsufficientFunds,
    InvalidMint,
    MintMismatch,
    OwnerMismatch,
    FixedSupply,
    AlreadyInUse,
    InvalidNumberOfProvidedSigners,
    InvalidNumberOfRequiredSigners,
    UninitializedState,
    NativeNotSupported,
    NonNativeHasBalance,
    InvalidInstruction,
    InvalidState,
    Overflow,
    AuthorityTypeNotSupported,
    MintCannotFreeze,
    AccountFrozen,
    MintDecimalsMismatch,
    NonNativeNotSupported,
]
CUSTOM_ERROR_MAP: dict[int, CustomError] = {
    0: NotRentExempt(),
    1: InsufficientFunds(),
    2: InvalidMint(),
    3: MintMismatch(),
    4: OwnerMismatch(),
    5: FixedSupply(),
    6: AlreadyInUse(),
    7: InvalidNumberOfProvidedSigners(),
    8: InvalidNumberOfRequiredSigners(),
    9: UninitializedState(),
    10: NativeNotSupported(),
    11: NonNativeHasBalance(),
    12: InvalidInstruction(),
    13: InvalidState(),
    14: Overflow(),
    15: AuthorityTypeNotSupported(),
    16: MintCannotFreeze(),
    17: AccountFrozen(),
    18: MintDecimalsMismatch(),
    19: NonNativeNotSupported(),
}


def from_code(code: int) -> typing.Optional[CustomError]:
    maybe_err = CUSTOM_ERROR_MAP.get(code)
    if maybe_err is None:
        return None
    return maybe_err
