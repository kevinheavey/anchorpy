import json
from pathlib import Path
from genpy import Suite
from anchorpy import Idl
from anchorpy.clientgen.instructions import gen_accounts
from anchorpy.clientgen.types import gen_struct


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


def test_empty_fields() -> None:
    path = Path("tests/idls/switchboard_v2.mainnet.06022022.json")
    with path.open() as f:
        data = json.load(f)
    idl = Idl.from_json(data)
    struct = gen_struct(idl, "AggregatorLockParams", [])
    assert str(struct) == (
        'import typing'  # noqa: P103
        '\nfrom dataclasses import dataclass'
        '\nfrom construct import Container, Construct'
        '\nfrom solana.publickey import PublicKey'
        '\nfrom anchorpy.borsh_extension import BorshPubkey'
        '\nimport borsh_construct as borsh'
        '\nclass AggregatorLockParamsJSON(typing.TypedDict):'
        '\n    pass'
        '\n@dataclass'
        '\nclass AggregatorLockParams():'
        '\n    layout: typing.ClassVar = borsh.CStruct()'
        '\n    @classmethod'
        '\n    def from_decoded(cls, obj: Container) -> "AggregatorLockParams":'
        '\n        return cls()'
        '\n    def to_encodable(self) -> dict[str, typing.Any]:'
        '\n        return {}'
        '\n    def to_json(self) -> AggregatorLockParamsJSON:'
        '\n        return {}'
        '\n    @classmethod'
        '\n    def from_json(cls, obj: AggregatorLockParamsJSON) -> "AggregatorLockParams":'
        '\n        return cls()'
    )
