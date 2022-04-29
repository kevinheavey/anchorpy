import * as GameState from "./GameState"
import * as Sign from "./Sign"

export { Tile, TileFields, TileJSON } from "./Tile"
export { GameState }

export type GameStateKind = GameState.Active | GameState.Tie | GameState.Won
export type GameStateJSON =
  | GameState.ActiveJSON
  | GameState.TieJSON
  | GameState.WonJSON

export { Sign }

export type SignKind = Sign.X | Sign.O
export type SignJSON = Sign.XJSON | Sign.OJSON
