from anchorpy import Coder, Idl
from anchorpy.program.context import Context
from anchorpy.program.namespace.instruction import _InstructionFn
from anchorpy.program.namespace.transaction import _build_transaction_fn
from pytest import fixture
from solders.instruction import Instruction
from solders.pubkey import Pubkey

DEFAULT_PUBKEY = Pubkey.default()


def _make_ix(data: bytes) -> Instruction:
    return Instruction(
        accounts=[],
        program_id=DEFAULT_PUBKEY,
        data=data,
    )


@fixture
def pre_ix() -> Instruction:
    return _make_ix(b"pre")


@fixture
def post_ix() -> Instruction:
    return _make_ix(b"post")


@fixture
def idl() -> Idl:
    raw = """{
        "version": "0.0.0",
        "name": "basic_0",
        "instructions": [
            {
                "name": "initialize",
                "accounts": [],
                "args": []
            }
        ]
    }"""
    return Idl.from_json(raw)


@fixture
def coder(idl: Idl) -> Coder:
    return Coder(idl)


def test_pre_instructions(coder: Coder, idl: Idl, pre_ix: Instruction) -> None:
    coder.instruction.encode
    ix_item = _InstructionFn(
        idl.instructions[0], coder.instruction.build, DEFAULT_PUBKEY
    )
    tx_item = _build_transaction_fn(idl.instructions[0], ix_item)
    tx = tx_item(ctx=Context(pre_instructions=[pre_ix]))
    assert len(tx.instructions) == 2
    assert tx.instructions[0] == pre_ix


def test_post_instructions(coder: Coder, idl: Idl, post_ix: Instruction) -> None:
    coder.instruction.encode
    ix_item = _InstructionFn(
        idl.instructions[0], coder.instruction.build, DEFAULT_PUBKEY
    )
    tx_item = _build_transaction_fn(idl.instructions[0], ix_item)
    tx = tx_item(ctx=Context(post_instructions=[post_ix]))
    assert len(tx.instructions) == 2
    assert tx.instructions[1] == post_ix
