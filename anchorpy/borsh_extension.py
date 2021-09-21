from construct import Adapter
from solana import publickey
from borsh import String


class _PublicKey(Adapter):
    def __init__(self) -> None:
        super().__init__(String)  # type: ignore

    def _decode(self, obj: str, context, path) -> publickey.PublicKey:
        return publickey.PublicKey(obj)

    def _encode(self, obj: publickey.PublicKey, context, path) -> str:
        return str(obj)


PublicKey = _PublicKey()
