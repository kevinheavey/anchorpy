"""The Python Anchor client."""
from contextlib import suppress as __suppress

from anchorpy_core.idl import Idl

from anchorpy import error, utils
from anchorpy.coder.coder import AccountsCoder, Coder, EventCoder, InstructionCoder
from anchorpy.idl import IdlProgramAccount
from anchorpy.program.common import (
    Event,
    NamedInstruction,
    translate_address,
    validate_accounts,
)
from anchorpy.program.context import Context
from anchorpy.program.core import Program
from anchorpy.program.event import EventParser
from anchorpy.program.namespace.account import AccountClient, ProgramAccount
from anchorpy.program.namespace.simulate import SimulateResponse
from anchorpy.provider import Provider, Wallet

__has_pytest = False
with __suppress(ImportError):
    from anchorpy.pytest_plugin import (
        bankrun_fixture,
        localnet_fixture,
        workspace_fixture,
    )

    __has_pytest = True
from anchorpy.workspace import WorkspaceType, close_workspace, create_workspace

__all_core = [
    "Program",
    "Provider",
    "Context",
    "create_workspace",
    "close_workspace",
    "Idl",
    "WorkspaceType",
    "Wallet",
    "Coder",
    "InstructionCoder",
    "EventCoder",
    "AccountsCoder",
    "NamedInstruction",
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

__all__ = (
    [
        *__all_core,
        "bankrun_fixture",
        "localnet_fixture",
        "workspace_fixture",
    ]
    if __has_pytest
    else __all_core
)

__version__ = "0.19.0"
