from pytest import mark
from anchorpy.workspace import create_workspace


@mark.integration
def test_init() -> None:
    """Test that the initialize function is invoked successfully."""
    workspace = create_workspace()
    program = workspace["basic_0"]
    res = program.rpc["initialize"]()
    assert res
