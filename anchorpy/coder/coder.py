from typing import Dict

from anchorpy.coder.common import sighash
from anchorpy.coder.accounts import AccountsCoder
from anchorpy.coder.event import EventCoder
from anchorpy.coder.instruction import InstructionCoder
from anchorpy.coder.state import StateCoder
from anchorpy.coder.types import TypesCoder
from anchorpy.idl import Idl


class Coder(object):
    def __init__(self, idl: Idl):
        self.instruction = InstructionCoder(idl)
        self.accounts = AccountsCoder(idl)
        self.types = TypesCoder(idl)
        self.events = EventCoder(idl)
        self.state = None
        if idl.state:
            self.state = StateCoder(idl)

    @staticmethod
    def sighash(namespace: str, ix_name: str) -> bytes:
        return sighash(namespace, ix_name)
