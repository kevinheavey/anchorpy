"""Provides the Coder class."""
from anchorpy.coder.accounts import AccountsCoder
from anchorpy.coder.event import EventCoder
from anchorpy.coder.instruction import InstructionCoder
from anchorpy.idl import Idl


class Coder:
    """Coder provides a facade for encoding and decoding all IDL related objects."""

    def __init__(self, idl: Idl):
        """Initialize the coder.

        Args:
            idl: a parsed Idl instance.
        """
        self.instruction: InstructionCoder = InstructionCoder(idl)
        self.accounts: AccountsCoder = AccountsCoder(idl)
        self.events: EventCoder = EventCoder(idl)
