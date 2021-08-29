from typing import Optional
from anchorpy.coder.accounts import AccountsCoder
from anchorpy.coder.event import EventCoder
from anchorpy.coder.instruction import InstructionCoder
from anchorpy.coder.state import StateCoder
from anchorpy.coder.types import TypesCoder
from anchorpy.idl import Idl


class Coder:
    def __init__(self, idl: Idl):
        self.instruction: InstructionCoder = InstructionCoder(idl)
        self.accounts: AccountsCoder = AccountsCoder(idl)
        self.types: TypesCoder = TypesCoder(idl)
        self.events: EventCoder = EventCoder(idl)
        self.state: Optional[StateCoder] = StateCoder(idl) if idl.state else None
