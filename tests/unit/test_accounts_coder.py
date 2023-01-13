from pathlib import Path

from anchorpy import AccountsCoder, Idl
from pytest import mark


@mark.unit
def test_accounts_coder() -> None:
    """Test accounts coder."""
    raw = Path("tests/idls/basic_1.json").read_text()
    idl = Idl.from_json(raw)
    raw_acc_data = b"\xf6\x1c\x06W\xfb-2*\xd2\x04\x00\x00\x00\x00\x00\x00"
    acc_coder = AccountsCoder(idl)
    decoded = acc_coder.parse(raw_acc_data)
    encoded = acc_coder.build(decoded)
    assert encoded == raw_acc_data
