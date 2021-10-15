from anchorpy.program.context import Context, check_args_length
from typing import Dict, Any, Tuple


from borsh_construct_tmp import CStruct
from construct import Sequence, Bytes
from construct import Construct, Adapter, Switch, Container
from anchorpy.coder.common import sighash
from anchorpy.program.common import to_instruction, InstructionToSerialize
from anchorpy.coder.idl import field_layout
from anchorpy.idl import Idl
from solana.keypair import Keypair
from solana.sysvar import SYSVAR_RENT_PUBKEY


SIGHASH_GLOBAL_NAMESPACE = "global"


class Sighash(Adapter):
    def __init__(self, namespace: str) -> None:
        super().__init__(Bytes(8))  # type: ignore
        self.namespace = namespace

    def _encode(self, obj: str, context, path) -> bytes:
        return sighash(self.namespace, obj)

    def _decode(self, obj: bytes, context, path):
        raise ValueError("Sighash cannot be reversed")


class InstructionCoder(Adapter):
    def __init__(self, idl: Idl) -> None:
        self.ix_layout = _parse_ix_layout(idl)
        sighasher = Sighash(SIGHASH_GLOBAL_NAMESPACE)
        sighash_layouts: Dict[bytes, Construct] = {}
        sighashes: Dict[str, bytes] = {}
        sighash_to_name: Dict[bytes, str] = {}
        for ix in idl.instructions:
            sh = sighasher.build(ix.name)
            sighashes[ix.name] = sh
            sighash_layouts[sh] = self.ix_layout[ix.name]
            sighash_to_name[sh] = ix.name
        self.sighash_layouts = sighash_layouts
        self.sighashes = sighashes
        self.sighash_to_name = sighash_to_name
        subcon = Sequence(
            "sighash" / Bytes(8),
            Switch(lambda this: this.sighash, sighash_layouts),
        )
        super().__init__(subcon)  # type: ignore

    def _decode(self, obj: Tuple[bytes, Any], context, path) -> InstructionToSerialize:
        return {"data": obj[1], "name": self.sighash_to_name[obj[0]]}

    def _encode(
        self, obj: InstructionToSerialize, context: Container, path
    ) -> Tuple[bytes, Any]:
        return (self.sighashes[obj["name"]], obj["data"])


def _parse_ix_layout(idl: Idl) -> Dict[str, Construct]:
    ix_layout: Dict[str, Construct] = {}
    for ix in idl.instructions:
        field_layouts = [field_layout(arg, idl.types) for arg in ix.args]
        ix_layout[ix.name] = ix.name / CStruct(*field_layouts)
    return ix_layout


if __name__ == "__main__":
    from json import loads
    from pathlib import Path

    data = loads((Path.home() / "anchorpy/idls/basic_1.json").read_text())
    idl = Idl.from_json(data)
    idl_ix = idl.instructions[0]
    my_account = Keypair()
    args = (1234,)
    ctx = Context(
        accounts={
            "myAccount": my_account.public_key,
            "rent": SYSVAR_RENT_PUBKEY,
        }
    )
    check_args_length(idl_ix, args)
    ix = to_instruction(idl_ix, args)
    coder = InstructionCoder(idl)
    encoded = coder.build(ix)
    assert encoded == b"\xaf\xafm\x1f\r\x98\x9b\xed\xd2\x04\x00\x00\x00\x00\x00\x00"
    assert coder.parse(encoded) == ix
