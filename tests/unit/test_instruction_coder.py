import json
from pathlib import Path

from anchorpy.idl import Idl
from anchorpy.program.context import check_args_length
from anchorpy.program.common import to_instruction
from anchorpy.coder.instruction import InstructionCoder


def test_instruction_coder() -> None:
    """Test InstructionCoder behaves as expected"""

    with Path("tests/idls/basic_1.json").open() as f:
        data = json.load(f)
    idl = Idl.from_json(data)
    idl_ix = idl.instructions[0]
    args = (1234,)
    check_args_length(idl_ix, args)
    ix = to_instruction(idl_ix, args)
    coder = InstructionCoder(idl)
    encoded = coder.build(ix)
    assert encoded == b"\xaf\xafm\x1f\r\x98\x9b\xed\xd2\x04\x00\x00\x00\x00\x00\x00"
    assert coder.parse(encoded) == ix
