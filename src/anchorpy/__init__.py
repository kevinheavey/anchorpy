"""The Python Anchor client."""
from anchorpy.provider import Provider, Wallet, SendTxRequest
from anchorpy.coder.coder import Coder, InstructionCoder, EventCoder, AccountsCoder
from anchorpy.idl import Idl, IdlProgramAccount
from anchorpy.workspace import create_workspace, close_workspace, WorkspaceType
from anchorpy.program.core import Program
from anchorpy.program.common import (
    Event,
    Instruction,
    translate_address,
    validate_accounts,
)
from anchorpy.program.context import Context
from anchorpy.program.namespace.account import AccountClient, ProgramAccount
from anchorpy.program.event import EventParser
from anchorpy.program.namespace.simulate import SimulateResponse
from anchorpy.pytest_plugin import localnet_fixture, workspace_fixture
from anchorpy import error, utils

__all__ = [
    "Program",
    "Provider",
    "Context",
    "create_workspace",
    "close_workspace",
    "Idl",
    "workspace_fixture",
    "WorkspaceType",
    "localnet_fixture",
    "Wallet",
    "SendTxRequest",
    "Coder",
    "InstructionCoder",
    "EventCoder",
    "AccountsCoder",
    "Instruction",
    "IdlProgramAccount",
    "Event",
    "translate_address",
    "validate_accounts",
    "AccountClient",
    "ProgramAccount",
    "EventParser",
    "SimulateResponse",
    "error",
    "utils",
]


__version__ = "0.11.0"
