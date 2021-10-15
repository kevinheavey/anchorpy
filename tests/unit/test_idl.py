import json
from pathlib import Path
from anchorpy.idl import Idl


def test_idls() -> None:
    idls = []
    for path in Path("tests/idls/").iterdir():
        with path.open() as f:
            data = json.load(f)
        idl = Idl.from_json(data)
        idls.append(idl)
    assert idls
