"""This module contains code for handling user-defined types."""
from typing import Type, Any
from anchorpy.coder.idl import _idl_typedef_to_python_type
from anchorpy.idl import Idl


def _build_types(
    idl: Idl,
) -> dict[str, Type[Any]]:
    """Generate the `.type` namespace.

    Args:
        idl: A parsed `Idl` instance.

    Returns:
        Mapping of type name to Python object.
    """
    result = {}
    for idl_type in idl.types:
        try:
            python_type = _idl_typedef_to_python_type(idl_type, idl.types)
        except ValueError:
            continue
        result[idl_type.name] = python_type
    return result
