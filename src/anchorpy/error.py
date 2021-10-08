class ProgramError(Exception):
    """An error from a user defined program."""

    def __init__(self, code: int, msg: str, *args: object) -> None:
        self.code = code
        self.msg = msg
        super().__init__(*args)
