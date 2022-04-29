import typing
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
import borsh_construct as borsh
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from ..program_id import PROGRAM_ID


class State2Fields(typing.TypedDict):
    vec_of_option: list[typing.Optional[int]]


class State2JSON(typing.TypedDict):
    vec_of_option: list[typing.Optional[int]]


class State2(object):
    discriminator = b"ja\xff\xa1\xfa\xcd\xb9\xc0"
    layout = borsh.CStruct("vec_of_option" / borsh.Vec(borsh.Option(borsh.U64)))

    def __init__(self, fields: State2Fields) -> None:
        self.vec_of_option = fields["vec_of_option"]

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: PublicKey,
        commitment: typing.Optional[Commitment] = None,
    ) -> typing.Optional["State2"]:
        resp = await conn.get_account_info(address, commitment=commitment)
        info = resp["result"]["value"]
        if info is None:
            return None
        if info["owner"] != str(PROGRAM_ID):
            raise ValueError("Account does not belong to this program")
        return cls.decode(info["data"])

    @classmethod
    async def fetch_multiple(
        cls,
        conn: AsyncClient,
        addresses: list[typing.Union[PublicKey, str]],
        commitment: typing.Optional[Commitment] = None,
    ) -> typing.List[typing.Optional["State2"]]:
        resp = await conn.get_multiple_accounts(addresses, commitment=commitment)
        infos = resp["result"]["value"]
        res: typing.List[typing.Optional["State2"]] = []
        for info in infos:
            if info is None:
                res.append(None)
            if info["owner"] != str(PROGRAM_ID):
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info["data"]))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "State2":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = State2.layout.decode(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            {
                "vec_of_option": dec.vec_of_option,
            }
        )

    def to_json(self) -> State2JSON:
        return {
            "vec_of_option": self.vec_of_option,
        }

    @classmethod
    def from_json(cls, obj: State2JSON) -> "State2":
        return cls(
            {
                "vec_of_option": obj["vec_of_option"],
            }
        )
