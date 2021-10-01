from anchorpy.idl import Idl
from hashlib import sha256


def event_discriminator(name: str) -> bytes:
    return sha256(f"event:{name}".encode()).digest()[:8]


class EventCoder(object):
    def __init__(self, idl: Idl):
        self.idl = idl
