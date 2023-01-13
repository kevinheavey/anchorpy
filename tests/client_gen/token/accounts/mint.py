import typing
from dataclasses import dataclass
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
import borsh_construct as borsh
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from anchorpy.utils.rpc import get_multiple_accounts
from anchorpy.borsh_extension import BorshPubkey, COption
from ..program_id import PROGRAM_ID


class MintJSON(typing.TypedDict):
    mint_authority: typing.Optional[str]
    supply: int
    decimals: int
    is_initialized: bool
    freeze_authority: typing.Optional[str]


@dataclass
class Mint:
    discriminator: typing.ClassVar = b"P\xbc\xf5\x14_\x8a9\x9c"
    layout: typing.ClassVar = borsh.CStruct(
        "mint_authority" / COption(BorshPubkey),
        "supply" / borsh.U64,
        "decimals" / borsh.U8,
        "is_initialized" / borsh.Bool,
        "freeze_authority" / COption(BorshPubkey),
    )
    mint_authority: typing.Optional[Pubkey]
    supply: int
    decimals: int
    is_initialized: bool
    freeze_authority: typing.Optional[Pubkey]

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["Mint"]:
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
    ) -> typing.List[typing.Optional["Mint"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["Mint"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "Mint":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = Mint.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            mint_authority=dec.mint_authority,
            supply=dec.supply,
            decimals=dec.decimals,
            is_initialized=dec.is_initialized,
            freeze_authority=dec.freeze_authority,
        )

    def to_json(self) -> MintJSON:
        return {
            "mint_authority": (
                None if self.mint_authority is None else str(self.mint_authority)
            ),
            "supply": self.supply,
            "decimals": self.decimals,
            "is_initialized": self.is_initialized,
            "freeze_authority": (
                None if self.freeze_authority is None else str(self.freeze_authority)
            ),
        }

    @classmethod
    def from_json(cls, obj: MintJSON) -> "Mint":
        return cls(
            mint_authority=(
                None
                if obj["mint_authority"] is None
                else Pubkey.from_string(obj["mint_authority"])
            ),
            supply=obj["supply"],
            decimals=obj["decimals"],
            is_initialized=obj["is_initialized"],
            freeze_authority=(
                None
                if obj["freeze_authority"] is None
                else Pubkey.from_string(obj["freeze_authority"])
            ),
        )
