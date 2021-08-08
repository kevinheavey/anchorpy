from __future__ import annotations

import hashlib
from typing import List, Tuple

from solana.publickey import PublicKey as OldPublicKey
from solana.utils import helpers


class PublicKey(OldPublicKey):
    @staticmethod
    def create_with_seed(from_public_key: PublicKey, seed: str, program_id: PublicKey) -> PublicKey:
        buf = bytes(from_public_key) + seed.encode("utf-8") + bytes(program_id)
        h = hashlib.sha256(buf)
        return PublicKey(h.digest())
