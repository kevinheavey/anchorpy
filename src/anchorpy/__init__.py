"""The Python Anchor client."""
from anchorpy.provider import Provider, LocalWallet
from anchorpy.coder.coder import Coder, InstructionCoder, EventCoder, AccountsCoder
from anchorpy.error import ProgramError
from anchorpy.coder.instruction import Instruction
from anchorpy.idl import Idl
from anchorpy.workspace import create_workspace, close_workspace
from anchorpy.program.core import Program
from anchorpy.program.context import Context
from anchorpy.program.namespace.account import AccountClient
from anchorpy.program.event import EventParser

__all__ = [
    "Provider",
    "LocalWallet",
    "Coder",
    "InstructionCoder",
    "EventCoder",
    "AccountsCoder",
    "ProgramError",
    "Instruction",
    "Idl",
    "create_workspace",
    "close_workspace",
    "Program",
    "Context",
    "AccountClient",
    "EventParser",
]

__version__ = "0.1.1"
