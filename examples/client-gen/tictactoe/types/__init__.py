from .tile import Tile, TileFields, TileJSON
from . import game_state
GameStateKind = Union[game_state.ActiveKind,game_state.TieKind,game_state.WonKind]
GameStateJSON = Union[game_state.ActiveJSON,game_state.TieJSON,game_state.WonJSON]
from . import sign
SignKind = Union[sign.XKind,sign.OKind]
SignJSON = Union[sign.XJSON,sign.OJSON]