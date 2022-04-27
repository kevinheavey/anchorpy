import typing
from .tile import Tile, TileFields, TileJSON
from . import game_state
from . import sign

GameStateKind = typing.Union[game_state.Active, game_state.Tie, game_state.Won]
GameStateJSON = typing.Union[
    game_state.ActiveJSON, game_state.TieJSON, game_state.WonJSON
]
SignKind = typing.Union[sign.X, sign.O]
SignJSON = typing.Union[sign.XJSON, sign.OJSON]
