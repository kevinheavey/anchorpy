import json
from pathlib import Path
from anchorpy.idl import Idl
from anchorpy.coder.accounts import AccountsCoder


def test_accounts_coder() -> None:
    """Test accounts coder"""
    with Path("tests/idls/basic_1.json").open() as f:
        data = json.load(f)
    idl = Idl.from_json(data)
    raw_acc_data = b"\xf6\x1c\x06W\xfb-2*\xd2\x04\x00\x00\x00\x00\x00\x00"
    acc_coder = AccountsCoder(idl)
    decoded = acc_coder.parse(raw_acc_data)
    encoded = acc_coder.build(decoded)
    assert encoded == raw_acc_data
