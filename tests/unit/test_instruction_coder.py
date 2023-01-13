from pathlib import Path

from anchorpy import Idl, InstructionCoder
from anchorpy.program.common import _to_instruction
from anchorpy.program.context import _check_args_length
from pytest import mark


@mark.unit
def test_instruction_coder() -> None:
    """Test InstructionCoder behaves as expected."""
    raw = Path("tests/idls/basic_1.json").read_text()
    idl = Idl.from_json(raw)
    idl_ix = idl.instructions[0]
    args = (1234,)
    _check_args_length(idl_ix, args)
    ix = _to_instruction(idl_ix, args)
    coder = InstructionCoder(idl)
    encoded = coder.build(ix)
    assert encoded == b"\xaf\xafm\x1f\r\x98\x9b\xed\xd2\x04\x00\x00\x00\x00\x00\x00"
    assert coder.parse(encoded) == ix
