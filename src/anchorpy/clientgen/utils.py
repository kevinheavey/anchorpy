from typing import Protocol
from pathlib import Path


class OutPath(Protocol):
    def __call__(self, path: str) -> Path:
        ...
