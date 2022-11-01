from anchorpy import Idl
from pathlib import Path
from pytest import mark
from solana.keypair import Keypair
from solana.transaction import AccountMeta

from anchorpy.program.namespace.instruction import _accounts_array


@mark.unit
def test_accounts_array() -> None:
    """Test accounts_array returns expected."""
    raw = Path("tests/idls/composite.json").read_text()
    idl = Idl.from_json(raw)
    dummy_a = Keypair.generate()
    dummy_b = Keypair.generate()
    comp_accounts = {
        "foo": {
            "dummy_a": dummy_a.public_key,
        },
        "bar": {
            "dummy_b": dummy_b.public_key,
        },
    }
    accounts_arg = idl.instructions[1].accounts
    acc_arr = _accounts_array(comp_accounts, accounts_arg)
    assert acc_arr == [
        AccountMeta(pubkey=dummy_a.public_key, is_signer=False, is_writable=True),
        AccountMeta(pubkey=dummy_b.public_key, is_signer=False, is_writable=True),
    ]
