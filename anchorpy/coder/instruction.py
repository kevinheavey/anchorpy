from anchorpy.program.context import split_args_and_context
from typing import Dict, Any
from dataclasses import asdict


from borsh import CStruct
from construct import Construct
from anchorpy.coder.common import sighash
from anchorpy.program.common import to_instruction
from anchorpy.coder.idl import field_layout
from anchorpy.idl import Idl
from solana.account import Account
from solana.sysvar import SYSVAR_RENT_PUBKEY


SIGHASH_GLOBAL_NAMESPACE = "global"


class InstructionCoder(object):
    def __init__(self, idl: Idl):
        self._ix_layout: Dict[str, Construct] = _parse_ix_layout(idl)

    def encode(self, ix_name: str, ix: Any) -> bytes:
        return self._encode(SIGHASH_GLOBAL_NAMESPACE, ix_name, ix)

    def _encode(self, namespace: str, ix_name: str, ix: Any) -> bytes:
        data = self._ix_layout[ix_name].build(ix)
        return sighash(namespace, ix_name) + data


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
    my_account = Account()
    args = (
        1234,
        {
            "accounts": {
                "myAccount": my_account.public_key(),
                "rent": SYSVAR_RENT_PUBKEY,
            }
        },
    )
    arg_list = list(args)
    split_args, ctx = split_args_and_context(idl_ix, arg_list)
    ix = to_instruction(idl_ix, split_args)
    encoded = InstructionCoder(idl).encode("initialize", ix)
    assert encoded == b"\xaf\xafm\x1f\r\x98\x9b\xed\xd2\x04\x00\x00\x00\x00\x00\x00"
    breakpoint()
