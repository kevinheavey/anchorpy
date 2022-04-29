import { TransactionInstruction, PublicKey } from "@solana/web3.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import BN from "bn.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as borsh from "@project-serum/borsh" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as types from "../types" // eslint-disable-line @typescript-eslint/no-unused-vars
import { PROGRAM_ID } from "../programId"

export interface PlayArgs {
  tile: types.TileFields
}

export interface PlayAccounts {
  game: PublicKey
  player: PublicKey
}

export const layout = borsh.struct([types.Tile.layout("tile")])

export function play(args: PlayArgs, accounts: PlayAccounts) {
  const keys = [
    { pubkey: accounts.game, isSigner: false, isWritable: true },
    { pubkey: accounts.player, isSigner: true, isWritable: false },
  ]
  const identifier = Buffer.from([213, 157, 193, 142, 228, 56, 248, 150])
  const buffer = Buffer.alloc(1000)
  const len = layout.encode(
    {
      tile: types.Tile.toEncodable(args.tile),
    },
    buffer
  )
  const data = Buffer.concat([identifier, buffer]).slice(0, 8 + len)
  const ix = new TransactionInstruction({ keys, programId: PROGRAM_ID, data })
  return ix
}
