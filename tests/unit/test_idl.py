from pathlib import Path

from anchorpy import Idl, Program
from solders.pubkey import Pubkey


def test_idls() -> None:
    idls = []
    programs = []
    for path in Path("tests/idls/").iterdir():
        raw = path.read_text()
        idl = Idl.from_json(raw)
        idls.append(idl)
        if "spl_token" not in str(path):
            program = Program(idl, Pubkey.default())
            programs.append(program)
    assert idls


def test_jet_enum() -> None:
    path = Path("tests/idls/jet.json")
    raw = path.read_text()
    idl = Idl.from_json(raw)
    program = Program(idl, Pubkey.default())
    expired_err = program.type["CacheInvalidError"].Expired
    assert expired_err(msg="hi").msg == "hi"


def test_switchboard_tuple() -> None:
    path = Path("tests/idls/switchboard.json")
    raw = path.read_text()
    idl = Idl.from_json(raw)
    program = Program(idl, Pubkey.default())  # noqa: F841


def test_clientgen_example() -> None:
    path = Path("tests/idls/clientgen_example_program.json")
    raw = path.read_text()
    Idl.from_json(raw)
