import typing
from dataclasses import dataclass
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
import borsh_construct as borsh
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from anchorpy.utils.rpc import get_multiple_accounts
from anchorpy.borsh_extension import BorshPubkey
from ..program_id import PROGRAM_ID


class MultisigJSON(typing.TypedDict):
    m: int
    n: int
    is_initialized: bool
    signers: list[str]


@dataclass
class Multisig:
    discriminator: typing.ClassVar = b"\xe0ty\xbaD\xa1O\xec"
    layout: typing.ClassVar = borsh.CStruct(
        "m" / borsh.U8,
        "n" / borsh.U8,
        "is_initialized" / borsh.Bool,
        "signers" / BorshPubkey[11],
    )
    m: int
    n: int
    is_initialized: bool
    signers: list[Pubkey]

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["Multisig"]:
        resp = await conn.get_account_info(address, commitment=commitment)
        info = resp.value
        if info is None:
            return None
        if info.owner != program_id:
            raise ValueError("Account does not belong to this program")
        bytes_data = info.data
        return cls.decode(bytes_data)

    @classmethod
    async def fetch_multiple(
        cls,
        conn: AsyncClient,
        addresses: list[Pubkey],
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.List[typing.Optional["Multisig"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["Multisig"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "Multisig":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = Multisig.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            m=dec.m,
            n=dec.n,
            is_initialized=dec.is_initialized,
            signers=dec.signers,
        )

    def to_json(self) -> MultisigJSON:
        return {
            "m": self.m,
            "n": self.n,
            "is_initialized": self.is_initialized,
            "signers": list(map(lambda item: str(item), self.signers)),
        }

    @classmethod
    def from_json(cls, obj: MultisigJSON) -> "Multisig":
        return cls(
            m=obj["m"],
            n=obj["n"],
            is_initialized=obj["is_initialized"],
            signers=list(map(lambda item: Pubkey.from_string(item), obj["signers"])),
        )
