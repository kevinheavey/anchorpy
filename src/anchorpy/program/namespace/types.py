"""This module contains code for handling user-defined types."""
from anchorpy.coder.idl import _idl_typedef_to_python_type
from anchorpy.idl import Idl


def _build_types(
    idl: Idl,
) -> dict[str, object]:
    """Generate the `.type` namespace.

    Args:
        idl: A parsed `Idl` instance.

    Returns:
        Mapping of type name to Python object.
    """
    return {
        idl_type.name: _idl_typedef_to_python_type(idl_type, idl.types)
        for idl_type in idl.types
    }
