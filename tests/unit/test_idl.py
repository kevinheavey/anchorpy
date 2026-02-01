from pathlib import Path

from anchorpy import Idl, Program, Provider
from solders.pubkey import Pubkey


def test_idls() -> None:
    idls = []
    programs = []
    for path in Path("tests/idls/").iterdir():
        raw = path.read_text()
        idl = Idl.from_json(raw)
        idls.append(idl)
        if "spl_token" not in str(path):
            program = Program(idl, Pubkey.default(), Provider.readonly())
            programs.append(program)
    assert idls


def test_clientgen_example() -> None:
    path = Path("tests/idls/clientgen_example_program.json")
    raw = path.read_text()
    Idl.from_json(raw)
