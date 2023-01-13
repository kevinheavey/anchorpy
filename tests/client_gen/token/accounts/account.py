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
from .. import types


class AccountJSON(typing.TypedDict):
    mint: str
    owner: str
    amount: int
    delegate: typing.Optional[str]
    state: types.account_state.AccountStateJSON
    is_native: typing.Optional[int]
    delegated_amount: int
    close_authority: typing.Optional[str]


@dataclass
class Account:
    discriminator: typing.ClassVar = b"qB\xe06\xbcw\xf0e"
    layout: typing.ClassVar = borsh.CStruct(
        "mint" / BorshPubkey,
        "owner" / BorshPubkey,
        "amount" / borsh.U64,
        "delegate" / COption(BorshPubkey),
        "state" / types.account_state.layout,
        "is_native" / COption(borsh.U64),
        "delegated_amount" / borsh.U64,
        "close_authority" / COption(BorshPubkey),
    )
    mint: Pubkey
    owner: Pubkey
    amount: int
    delegate: typing.Optional[Pubkey]
    state: types.account_state.AccountStateKind
    is_native: typing.Optional[int]
    delegated_amount: int
    close_authority: typing.Optional[Pubkey]

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["Account"]:
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
    ) -> typing.List[typing.Optional["Account"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["Account"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "Account":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = Account.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            mint=dec.mint,
            owner=dec.owner,
            amount=dec.amount,
            delegate=dec.delegate,
            state=types.account_state.from_decoded(dec.state),
            is_native=dec.is_native,
            delegated_amount=dec.delegated_amount,
            close_authority=dec.close_authority,
        )

    def to_json(self) -> AccountJSON:
        return {
            "mint": str(self.mint),
            "owner": str(self.owner),
            "amount": self.amount,
            "delegate": (None if self.delegate is None else str(self.delegate)),
            "state": self.state.to_json(),
            "is_native": self.is_native,
            "delegated_amount": self.delegated_amount,
            "close_authority": (
                None if self.close_authority is None else str(self.close_authority)
            ),
        }

    @classmethod
    def from_json(cls, obj: AccountJSON) -> "Account":
        return cls(
            mint=Pubkey.from_string(obj["mint"]),
            owner=Pubkey.from_string(obj["owner"]),
            amount=obj["amount"],
            delegate=(
                None if obj["delegate"] is None else Pubkey.from_string(obj["delegate"])
            ),
            state=types.account_state.from_json(obj["state"]),
            is_native=obj["is_native"],
            delegated_amount=obj["delegated_amount"],
            close_authority=(
                None
                if obj["close_authority"] is None
                else Pubkey.from_string(obj["close_authority"])
            ),
        )
