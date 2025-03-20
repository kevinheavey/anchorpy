"""The TypesCoder class is for encoding and decoding user-defined types."""

from typing import Any, Dict

from anchorpy_core.idl import Idl
from construct import Construct, Container

from anchorpy.coder.idl import _typedef_layout_without_field_name


class TypesCoder:
    """Encodes and decodes user-defined types in Anchor programs."""

    def __init__(self, idl: Idl) -> None:
        """Initialize the TypesCoder.

        Args:
            idl: The parsed IDL object.
        """
        self.idl = idl
        self.types_layouts: Dict[str, Construct] = {}

        if idl.types:
            filtered_types = [
                ty for ty in idl.types if not getattr(ty, "generics", None)
            ]

            for type_def in filtered_types:
                self.types_layouts[type_def.name] = _typedef_layout_without_field_name(
                    type_def, idl.types
                )

    def encode(self, name: str, data: Any) -> bytes:
        """Encode a user-defined type.

        Args:
            name: The name of the type.
            data: The data to encode.

        Returns:
            The encoded data.

        Raises:
            ValueError: If the type is not found.
        """
        layout = self.types_layouts.get(name)
        if not layout:
            raise ValueError(f"Unknown type: {name}")

        return layout.build(data)

    def decode(self, name: str, buffer: bytes) -> Container[Any]:
        """Decode a user-defined type.

        Args:
            name: The name of the type.
            buffer: The buffer to decode.

        Returns:
            The decoded data.

        Raises:
            ValueError: If the type is not found.
        """
        layout = self.types_layouts.get(name)
        if not layout:
            raise ValueError(f"Unknown type: {name}")

        return layout.parse(buffer)
