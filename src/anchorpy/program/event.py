from dataclasses import dataclass
from base64 import b64decode
from typing import Callable, List, NamedTuple, Optional, Tuple, cast
import binascii
from solana.publickey import PublicKey
from anchorpy.coder.coder import Coder


LOG_START_INDEX = len("Program log: ")


class Event(NamedTuple):
    name: str
    data: dict


class ExecutionContext:
    def __init__(self, log: str) -> None:
        try:
            program = log.split("Program ")[1].split(" invoke [")[0]
        except IndexError as e:
            raise ValueError("Could not find program invocation log line") from e
        self.stack = [program]

    def program(self) -> str:
        return self.stack[-1]

    def push(self, new_program: str) -> None:
        self.stack.append(new_program)

    def pop(self) -> None:
        self.stack.pop()


@dataclass
class EventParser:
    program_id: PublicKey
    coder: Coder

    def parse_logs(self, logs: List[str], callback: Callable[[Event], None]) -> None:
        log_scanner = LogScanner(logs)
        execution = ExecutionContext(cast(str, log_scanner.to_next()))
        log = log_scanner.to_next()
        while log is not None:
            event, new_program, did_pop = self.handle_log(execution, log)
            if event is not None:
                callback(event)
            if new_program is not None:
                execution.push(new_program)
            if did_pop:
                execution.pop()
            log = log_scanner.to_next()

    def handle_log(
        self, execution: ExecutionContext, log: str
    ) -> Tuple[Optional[Event], Optional[str], bool]:
        # Executing program is this program.
        if execution.stack and execution.program() == str(self.program_id):
            return self.handle_program_log(log)
        # Executing program is not this program.
        return (None, *self.handle_system_log(log))

    def handle_program_log(
        self, log: str
    ) -> Tuple[Optional[Event], Optional[str], bool]:
        # This is a `msg!` log.
        if log.startswith("Program log:"):
            log_str = log[LOG_START_INDEX:]
            try:
                decoded = b64decode(log_str)
            except binascii.Error:
                return None, None, False
            event = self.coder.events.parse(decoded)
            return event, None, False
        return (None, *self.handle_system_log(log))

    def handle_system_log(self, log: str) -> Tuple[Optional[str], bool]:
        log_start = log.split(":")[0]
        if log_start.split("Program ")[1].split(" ")[1] == "success":
            return None, True
        elif log_start.startswith(f"Program {str(self.program_id)} invoke"):
            return str(self.program_id), False
        elif "invoke" in log_start:
            return "cpi", False
        return None, False


@dataclass
class LogScanner:
    logs: List[str]

    def to_next(self) -> Optional[str]:
        if self.logs:
            log = self.logs[0]
            self.logs = self.logs[1:]
            return log
        return None
