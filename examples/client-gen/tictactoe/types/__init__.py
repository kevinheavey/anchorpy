from typing import Union
from .tile import Tile, TileFields, TileJSON
from . import game_state
from . import sign

GameStateKind = typing.Union[
    game_state.ActiveKind, game_state.TieKind, game_state.WonKind
]
GameStateJSON = typing.Union[
    game_state.ActiveJSON, game_state.TieJSON, game_state.WonJSON
]
SignKind = typing.Union[sign.XKind, sign.OKind]
SignJSON = typing.Union[sign.XJSON, sign.OJSON]
