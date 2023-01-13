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


class BaseAccountJSON(typing.TypedDict):
    base_data: int
    base_data_key: str


@dataclass
class BaseAccount:
    discriminator: typing.ClassVar = b"\x10Z\x82\xf2\x9f\n\xe8\x85"
    layout: typing.ClassVar = borsh.CStruct(
        "base_data" / borsh.U64, "base_data_key" / BorshPubkey
    )
    base_data: int
    base_data_key: Pubkey

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["BaseAccount"]:
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
    ) -> typing.List[typing.Optional["BaseAccount"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["BaseAccount"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "BaseAccount":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = BaseAccount.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            base_data=dec.base_data,
            base_data_key=dec.base_data_key,
        )

    def to_json(self) -> BaseAccountJSON:
        return {
            "base_data": self.base_data,
            "base_data_key": str(self.base_data_key),
        }

    @classmethod
    def from_json(cls, obj: BaseAccountJSON) -> "BaseAccount":
        return cls(
            base_data=obj["base_data"],
            base_data_key=Pubkey.from_string(obj["base_data_key"]),
        )
