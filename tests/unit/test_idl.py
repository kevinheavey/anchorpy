import json
from pathlib import Path
from pytest import mark
from anchorpy import Idl, Program
from solana.publickey import PublicKey


@mark.unit
def test_idls() -> None:
    idls = []
    programs = []
    for path in Path("tests/idls/").iterdir():
        with path.open() as f:
            data = json.load(f)
        idl = Idl.from_json(data)
        idls.append(idl)
        program = Program(idl, PublicKey(1))
        programs.append(program)
    assert idls


@mark.unit
def test_jet_enum() -> None:
    path = Path("tests/idls/jet.json")
    with path.open() as f:
        data = json.load(f)
    idl = Idl.from_json(data)
    program = Program(idl, PublicKey(1))
    cache_invalid_err = program.type["CacheInvalidError"]
    assert cache_invalid_err.Expired(msg="hi").msg == "hi"
    assert cache_invalid_err.Expired._sumtype_attribs[0][1].type == str
