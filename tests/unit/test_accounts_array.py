from pathlib import Path

from anchorpy import Idl
from anchorpy.program.namespace.instruction import _accounts_array
from pytest import mark
from solana.transaction import AccountMeta
from solders.keypair import Keypair


@mark.unit
def test_accounts_array() -> None:
    """Test accounts_array returns expected."""
    raw = Path("tests/idls/composite.json").read_text()
    idl = Idl.from_json(raw)
    dummy_a = Keypair()
    dummy_b = Keypair()
    comp_accounts = {
        "foo": {
            "dummy_a": dummy_a.pubkey(),
        },
        "bar": {
            "dummy_b": dummy_b.pubkey(),
        },
    }
    accounts_arg = idl.instructions[1].accounts
    acc_arr = _accounts_array(comp_accounts, accounts_arg)
    assert acc_arr == [
        AccountMeta(pubkey=dummy_a.pubkey(), is_signer=False, is_writable=True),
        AccountMeta(pubkey=dummy_b.pubkey(), is_signer=False, is_writable=True),
    ]
