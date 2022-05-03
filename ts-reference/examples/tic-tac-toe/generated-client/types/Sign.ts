import { PublicKey } from "@solana/web3.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import BN from "bn.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as types from "../types" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as borsh from "@project-serum/borsh"

export interface XJSON {
  kind: "X"
}

export class X {
  readonly discriminator = 0
  readonly kind = "X"

  toJSON(): XJSON {
    return {
      kind: "X",
    }
  }

  toEncodable() {
    return {
      X: {},
    }
  }
}

export interface OJSON {
  kind: "O"
}

export class O {
  readonly discriminator = 1
  readonly kind = "O"

  toJSON(): OJSON {
    return {
      kind: "O",
    }
  }

  toEncodable() {
    return {
      O: {},
    }
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function fromDecoded(obj: any): types.SignKind {
  if (typeof obj !== "object") {
    throw new Error("Invalid enum object")
  }

  if ("X" in obj) {
    return new X()
  }
  if ("O" in obj) {
    return new O()
  }

  throw new Error("Invalid enum object")
}

export function fromJSON(obj: types.SignJSON): types.SignKind {
  switch (obj.kind) {
    case "X": {
      return new X()
    }
    case "O": {
      return new O()
    }
  }
}

export function layout(property?: string) {
  const ret = borsh.rustEnum([borsh.struct([], "X"), borsh.struct([], "O")])
  if (property !== undefined) {
    return ret.replicate(property)
  }
  return ret
}
