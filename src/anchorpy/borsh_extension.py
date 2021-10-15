"""Extensions to the Borsh spec for Solana-specific types."""
from solana import publickey
from construct import Bytes, Adapter


class _PublicKey(Adapter):
    def __init__(self) -> None:
        super().__init__(Bytes(32))  # type: ignore

    def _decode(self, obj: bytes, context, path) -> publickey.PublicKey:
        return publickey.PublicKey(obj)

    def _encode(self, obj: publickey.PublicKey, context, path) -> bytes:
        return bytes(obj)


PublicKey = _PublicKey()
