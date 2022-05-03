import { PublicKey } from "@solana/web3.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import BN from "bn.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as types from "../types" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as borsh from "@project-serum/borsh"

export interface TileFields {
  row: number
  column: number
}

export interface TileJSON {
  row: number
  column: number
}

export class Tile {
  readonly row: number
  readonly column: number

  constructor(fields: TileFields) {
    this.row = fields.row
    this.column = fields.column
  }

  static layout(property?: string) {
    return borsh.struct([borsh.u8("row"), borsh.u8("column")], property)
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  static fromDecoded(obj: any) {
    return new Tile({
      row: obj.row,
      column: obj.column,
    })
  }

  static toEncodable(fields: TileFields) {
    return {
      row: fields.row,
      column: fields.column,
    }
  }

  toJSON(): TileJSON {
    return {
      row: this.row,
      column: this.column,
    }
  }

  static fromJSON(obj: TileJSON): Tile {
    return new Tile({
      row: obj.row,
      column: obj.column,
    })
  }

  toEncodable() {
    return Tile.toEncodable(this)
  }
}
