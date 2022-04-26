import json
from pathlib import Path
from genpy import Suite
from anchorpy import Idl
from anchorpy.clientgen.instructions import gen_accounts


def test_gen_accounts() -> None:
    path = Path("tests/idls/composite.json")
    with path.open() as f:
        data = json.load(f)
    idl = Idl.from_json(data)
    accs = gen_accounts("CompositeUpdateAccounts", idl.instructions[1].accounts)
    suite = Suite(accs)
    assert str(suite) == (
        "    class CompositeUpdateAccounts(typing.TypedDict):"
        "\n        foo: FooNested"
        "\n        bar: BarNested"
        "\n    class FooNested(typing.TypedDict):"
        "\n        dummy_a: PublicKey"
        "\n    class BarNested(typing.TypedDict):"
        "\n        dummy_b: PublicKey"
        "\n    class FooNested(typing.TypedDict):"
        "\n        dummy_a: PublicKey"
    )
