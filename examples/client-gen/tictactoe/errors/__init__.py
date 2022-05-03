import typing
import re
from solana.rpc.core import RPCException
from ..program_id import PROGRAM_ID
from . import anchor
from . import custom


def from_code(code: int) -> typing.Union[custom.CustomError, anchor.AnchorError, None]:
    return custom.from_code(code) if code >= 6000 else anchor.from_code(code)


error_re = re.compile(r"Program (\w+) failed: custom program error: (\w+)")


def _find_first_match(logs: list[str]) -> typing.Optional[re.Match]:
    for logline in logs:
        first_match = error_re.match(logline)
        if first_match is not None:
            return first_match
    return None


def from_tx_error(
    error: RPCException,
) -> typing.Union[anchor.AnchorError, custom.CustomError, None]:
    err_info = error.args[0]
    if "data" not in err_info:
        return None
    if "logs" not in err_info["data"]:
        return None
    first_match = _find_first_match(err_info["data"]["logs"])
    if first_match is None:
        return None
    program_id_raw, code_raw = first_match.groups()
    if program_id_raw != str(PROGRAM_ID):
        return None
    try:
        error_code = int(code_raw, 16)
    except ValueError:
        return None
    return from_code(error_code)
