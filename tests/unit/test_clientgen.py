from pathlib import Path

from anchorpy import Idl
from anchorpy.clientgen.instructions import gen_accounts
from anchorpy.clientgen.types import gen_struct
from genpy import Suite


def test_gen_accounts() -> None:
    path = Path("tests/idls/composite.json")
    raw = path.read_text()
    idl = Idl.from_json(raw)
    accs = gen_accounts(
        "CompositeUpdateAccounts", idl.instructions[1].accounts, gen_pdas=True
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


def test_empty_fields() -> None:
    path = Path("tests/idls/switchboard_v2.mainnet.06022022.json")
    raw = path.read_text()
    idl = Idl.from_json(raw)
    struct = gen_struct(idl, "AggregatorLockParams", [])
    assert str(struct) == (
        "import typing"
        "\nfrom dataclasses import dataclass"
        "\nfrom construct import Container, Construct"
        "\nfrom solders.pubkey import Pubkey"
        "\nfrom anchorpy.borsh_extension import BorshPubkey"
        "\nimport borsh_construct as borsh"
        "\nclass AggregatorLockParamsJSON(typing.TypedDict):"
        "\n    pass"
        "\n@dataclass"
        "\nclass AggregatorLockParams():"
        "\n    layout: typing.ClassVar = borsh.CStruct()"
        "\n    @classmethod"
        '\n    def from_decoded(cls, obj: Container) -> "AggregatorLockParams":'
        "\n        return cls()"
        "\n    def to_encodable(self) -> dict[str, typing.Any]:"
        "\n        return {}"
        "\n    def to_json(self) -> AggregatorLockParamsJSON:"
        "\n        return {}"
        "\n    @classmethod"
        '\n    def from_json(cls, obj: AggregatorLockParamsJSON) -> "AggregatorLockParams":'
        "\n        return cls()"
    )
