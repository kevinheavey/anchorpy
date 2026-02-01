from pathlib import Path

from anchorpy import Idl
from anchorpy.clientgen.instructions import gen_accounts
from genpy import Suite


def test_gen_accounts() -> None:
    path = Path("tests/idls/composite.json")
    raw = path.read_text()
    idl = Idl.from_json(raw)
    accs = gen_accounts(
        "CompositeUpdateAccounts", idl.instructions[0].accounts, gen_pdas=True
    )[0]
    suite = Suite(accs)
    assert str(suite) == (
        "    class CompositeUpdateAccounts(typing.TypedDict):"
        "\n        foo: FooNested"
        "\n        bar: BarNested"
        "\n    class FooNested(typing.TypedDict):"
        "\n        dummy_a: Pubkey"
        "\n    class BarNested(typing.TypedDict):"
        "\n        dummy_b: Pubkey"
        "\n    class FooNested(typing.TypedDict):"
        "\n        dummy_a: Pubkey"
    )
