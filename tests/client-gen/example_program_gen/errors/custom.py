import typing
from anchorpy.error import ProgramError


class SomeError(ProgramError):
    def __init__(self) -> None:
        super().__init__(6000, "Example error.")

    code = 6000
    name = "SomeError"
    msg = "Example error."


class OtherError(ProgramError):
    def __init__(self) -> None:
        super().__init__(6001, "Another error.")

    code = 6001
    name = "OtherError"
    msg = "Another error."


CustomError = typing.Union[SomeError, OtherError]
CUSTOM_ERROR_MAP: dict[int, CustomError] = {
    6000: SomeError(),
    6001: OtherError(),
}


def from_code(code: int) -> typing.Optional[CustomError]:
    maybe_err = CUSTOM_ERROR_MAP.get(code)
    if maybe_err is None:
        return None
    return maybe_err
