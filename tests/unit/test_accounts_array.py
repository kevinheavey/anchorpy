from anchorpy.idl import Idl
from pathlib import Path
import json
from solana.keypair import Keypair
from solana.transaction import AccountMeta

from anchorpy.program.namespace.instruction import accounts_array


def test_accounts_array() -> None:
    """Test accounts_array returns expected."""

    with Path("tests/idls/composite.json").open() as f:
        idl_json = json.load(f)
    idl = Idl.from_json(idl_json)
    dummy_a = Keypair.generate()
    dummy_b = Keypair.generate()
    comp_accounts = {
        "foo": {
            "dummyA": dummy_a.public_key,
        },
        "bar": {
            "dummyB": dummy_b.public_key,
        },
    }
    accounts_arg = idl.instructions[1].accounts
    acc_arr = accounts_array(comp_accounts, accounts_arg)
    assert acc_arr == [
        AccountMeta(pubkey=dummy_a.public_key, is_signer=False, is_writable=True),
        AccountMeta(pubkey=dummy_b.public_key, is_signer=False, is_writable=True),
    ]
