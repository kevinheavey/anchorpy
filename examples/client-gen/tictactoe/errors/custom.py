import typing
from anchorpy.error import ProgramError


class TileOutOfBounds(ProgramError):
    def __init__(self) -> None:
        super().__init__(6000, None)

    code = 6000
    name = "TileOutOfBounds"
    msg = None


class TileAlreadySet(ProgramError):
    def __init__(self) -> None:
        super().__init__(6001, None)

    code = 6001
    name = "TileAlreadySet"
    msg = None


class GameAlreadyOver(ProgramError):
    def __init__(self) -> None:
        super().__init__(6002, None)

    code = 6002
    name = "GameAlreadyOver"
    msg = None


class NotPlayersTurn(ProgramError):
    def __init__(self) -> None:
        super().__init__(6003, None)

    code = 6003
    name = "NotPlayersTurn"
    msg = None


class GameAlreadyStarted(ProgramError):
    def __init__(self) -> None:
        super().__init__(6004, None)

    code = 6004
    name = "GameAlreadyStarted"
    msg = None


CustomError = typing.Union[
    TileOutOfBounds, TileAlreadySet, GameAlreadyOver, NotPlayersTurn, GameAlreadyStarted
]
CUSTOM_ERROR_MAP: dict[int, CustomError] = {
    6000: TileOutOfBounds(),
    6001: TileAlreadySet(),
    6002: GameAlreadyOver(),
    6003: NotPlayersTurn(),
    6004: GameAlreadyStarted(),
}


def from_code(code: int) -> typing.Optional[CustomError]:
    maybe_err = CUSTOM_ERROR_MAP.get(code)
    if maybe_err is None:
        return None
    return maybe_err
