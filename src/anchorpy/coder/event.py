from anchorpy.coder.idl import typedef_layout
from hashlib import sha256
from typing import Dict, Tuple, Any
from construct import Adapter, Construct, Sequence, Bytes, Switch
from anchorpy.idl import Idl, IdlEvent, IdlField, IdlTypeDef, IdlTypeDefTyStruct
from anchorpy.program.common import Instruction


def event_discriminator(name: str) -> bytes:
    return sha256(f"event:{name}".encode()).digest()[:8]


def _event_layout(event: IdlEvent, idl: Idl) -> Construct:
    event_type_def = IdlTypeDef(
        name=event.name,
        type=IdlTypeDefTyStruct(
            fields=[IdlField(name=f.name, type=f.type) for f in event.fields]
        ),
    )
    return typedef_layout(event_type_def, idl.types)


class EventCoder(Adapter):
    """Encodes and decodes Anchor events."""

    def __init__(self, idl: Idl):
        self.idl = idl
        idl_events = idl.events
        layouts: Dict[str, Construct]
        if idl_events:
            layouts = {event.name: _event_layout(event, idl) for event in idl_events}
        else:
            layouts = {}
        self.layouts = layouts
        self.discriminators: Dict[bytes, str] = {
            event_discriminator(event.name): event.name for event in idl_events
        }
        self.discriminator_to_layout = {
            disc: self.layouts[event_name]
            for disc, event_name in self.discriminators.items()
        }
        subcon = Sequence(
            "discriminator" / Bytes(8),  # not base64-encoded here
            Switch(lambda this: this.discriminator, self.discriminator_to_layout),
        )
        super().__init__(subcon)  # type: ignore

    def _decode(self, obj: Tuple[bytes, Any], context, path) -> Instruction:
        disc = obj[0]  # check this, might need more decoding
        event_name = self.discriminators[disc]
        return {"data": obj[1], "name": event_name}
