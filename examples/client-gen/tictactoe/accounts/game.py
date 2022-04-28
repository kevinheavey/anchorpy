import typing
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
import borsh_construct as borsh
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from anchorpy.borsh_extension import BorshPubkey, EnumForCodegen
from ..program_id import PROGRAM_ID
from .. import types


class GameFields(typing.TypedDict):
    players: list[PublicKey]
    turn: int
    board: list[list[typing.Optional[types.SignKind]]]
    state: types.GameStateKind


class GameJSON(typing.TypedDict):
    players: list[str]
    turn: int
    board: list[list[typing.Optional[types.SignJSON]]]
    state: types.GameStateJSON


class Game(object):
    discriminator = b"\x1bZ\xa6}Jdy\x12"
    layout = borsh.CStruct(
        "players" / BorshPubkey[2],
        "turn" / borsh.U8,
        "board" / borsh.Option(types.sign.layout())[3][3],
        "state" / types.game_state.layout(),
    )

    def __init__(self, fields: GameFields) -> None:
        self.players = fields["players"]
        self.turn = fields["turn"]
        self.board = fields["board"]
        self.state = fields["state"]

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: PublicKey,
        commitment: typing.Optional[Commitment] = None,
    ) -> typing.Optional["Game"]:
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
        addresses: list[PublicKey],
        commitment: typing.Optional[Commitment] = None,
    ) -> list[typing.Optional["Game"]]:
        resp = await conn.get_account_info(address, commitment=commitment)
        infos = resp["result"]["value"]
        res = []
        for info in infos:
            if info is None:
                return None
            if info["owner"] != str(PROGRAM_ID):
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info["data"]))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "Game":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = Game.layout.decode(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            {
                "players": dec.players,
                "turn": dec.turn,
                "board": list(
                    map(
                        lambda item: list(
                            map(
                                lambda item: (item and types.Sign.from_decoded(item))
                                or None,
                                item,
                            )
                        ),
                        dec.board,
                    )
                ),
                "state": types.GameState.from_decoded(dec.state),
            }
        )

    def to_json(self) -> GameJSON:
        return {
            "players": list(map(lambda item: str(item), self.players)),
            "turn": self.turn,
            "board": list(
                map(
                    lambda item: list(
                        map(lambda item: (item and item.to_json()) or None, item)
                    ),
                    self.board,
                )
            ),
            "state": self.state.to_json(),
        }

    @classmethod
    def from_json(cls, obj: GameJSON) -> "Game":
        return cls(
            {
                "players": list(map(lambda item: PublicKey(item), obj["players"])),
                "turn": obj["turn"],
                "board": list(
                    map(
                        lambda item: list(
                            map(
                                lambda item: (item and types.item.from_json(item))
                                or None,
                                item,
                            )
                        ),
                        obj["board"],
                    )
                ),
                "state": types.state.from_json(obj["state"]),
            }
        )
