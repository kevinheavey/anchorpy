import { PublicKey, Connection } from "@solana/web3.js"
import BN from "bn.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as borsh from "@project-serum/borsh" // eslint-disable-line @typescript-eslint/no-unused-vars
import { PROGRAM_ID } from "../programId"

export interface CounterFields {
  authority: PublicKey
  count: BN
}

export interface CounterJSON {
  authority: string
  count: string
}

export class Counter {
  readonly authority: PublicKey
  readonly count: BN

  static readonly discriminator = Buffer.from([
    255, 176, 4, 245, 188, 253, 124, 25,
  ])

  static readonly layout = borsh.struct([
    borsh.publicKey("authority"),
    borsh.u64("count"),
  ])

  constructor(fields: CounterFields) {
    this.authority = fields.authority
    this.count = fields.count
  }

  static async fetch(
    c: Connection,
    address: PublicKey
  ): Promise<Counter | null> {
    const info = await c.getAccountInfo(address)

    if (info === null) {
      return null
    }
    if (!info.owner.equals(PROGRAM_ID)) {
      throw new Error("account doesn't belong to this program")
    }

    return this.decode(info.data)
  }

  static async fetchMultiple(
    c: Connection,
    addresses: PublicKey[]
  ): Promise<Array<Counter | null>> {
    const infos = await c.getMultipleAccountsInfo(addresses)

    return infos.map((info) => {
      if (info === null) {
        return null
      }
      if (!info.owner.equals(PROGRAM_ID)) {
        throw new Error("account doesn't belong to this program")
      }

      return this.decode(info.data)
    })
  }

  static decode(data: Buffer): Counter {
    if (!data.slice(0, 8).equals(Counter.discriminator)) {
      throw new Error("invalid account discriminator")
    }

    const dec = Counter.layout.decode(data.slice(8))

    return new Counter({
      authority: dec.authority,
      count: dec.count,
    })
  }

  toJSON(): CounterJSON {
    return {
      authority: this.authority.toString(),
      count: this.count.toString(),
    }
  }

  static fromJSON(obj: CounterJSON): Counter {
    return new Counter({
      authority: new PublicKey(obj.authority),
      count: new BN(obj.count),
    })
  }
}
