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

        self.filtered_types = []
        if idl.types:
            self.filtered_types = [
                ty for ty in idl.types if not getattr(ty, "generics", None)
            ]

    def _get_layout(self, name: str) -> Construct:
        """Get or create a layout for a given type name.

        Args:
            name: The name of the type.

        Returns:
            The construct layout for the type.

        Raises:
            ValueError: If the type is not found.
        """
        if name in self.types_layouts:
            return self.types_layouts[name]

        type_defs = [t for t in self.filtered_types if t.name == name]
        if not type_defs:
            raise ValueError(f"Unknown type: {name}")

        layout = _typedef_layout_without_field_name(type_defs[0], self.idl.types)
        self.types_layouts[name] = layout
        return layout

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
        layout = self._get_layout(name)
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
        layout = self._get_layout(name)
        return layout.parse(buffer)
