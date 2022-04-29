import { PublicKey } from "@solana/web3.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import BN from "bn.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as types from "../types" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as borsh from "@project-serum/borsh"

export type UnnamedFields = [boolean, number, types.BarStructFields]
export type UnnamedValue = [boolean, number, types.BarStruct]

export interface UnnamedJSON {
  kind: "Unnamed"
  value: [boolean, number, types.BarStructJSON]
}

export class Unnamed {
  readonly discriminator = 0
  readonly kind = "Unnamed"
  readonly value: UnnamedValue

  constructor(value: UnnamedFields) {
    this.value = [value[0], value[1], new types.BarStruct({ ...value[2] })]
  }

  toJSON(): UnnamedJSON {
    return {
      kind: "Unnamed",
      value: [this.value[0], this.value[1], this.value[2].toJSON()],
    }
  }

  toEncodable() {
    return {
      Unnamed: {
        _0: this.value[0],
        _1: this.value[1],
        _2: types.BarStruct.toEncodable(this.value[2]),
      },
    }
  }
}

export type UnnamedSingleFields = [types.BarStructFields]
export type UnnamedSingleValue = [types.BarStruct]

export interface UnnamedSingleJSON {
  kind: "UnnamedSingle"
  value: [types.BarStructJSON]
}

export class UnnamedSingle {
  readonly discriminator = 1
  readonly kind = "UnnamedSingle"
  readonly value: UnnamedSingleValue

  constructor(value: UnnamedSingleFields) {
    this.value = [new types.BarStruct({ ...value[0] })]
  }

  toJSON(): UnnamedSingleJSON {
    return {
      kind: "UnnamedSingle",
      value: [this.value[0].toJSON()],
    }
  }

  toEncodable() {
    return {
      UnnamedSingle: {
        _0: types.BarStruct.toEncodable(this.value[0]),
      },
    }
  }
}

export type NamedFields = {
  boolField: boolean
  u8Field: number
  nested: types.BarStructFields
}
export type NamedValue = {
  boolField: boolean
  u8Field: number
  nested: types.BarStruct
}

export interface NamedJSON {
  kind: "Named"
  value: {
    boolField: boolean
    u8Field: number
    nested: types.BarStructJSON
  }
}

export class Named {
  readonly discriminator = 2
  readonly kind = "Named"
  readonly value: NamedValue

  constructor(value: NamedFields) {
    this.value = {
      boolField: value.boolField,
      u8Field: value.u8Field,
      nested: new types.BarStruct({ ...value.nested }),
    }
  }

  toJSON(): NamedJSON {
    return {
      kind: "Named",
      value: {
        boolField: this.value.boolField,
        u8Field: this.value.u8Field,
        nested: this.value.nested.toJSON(),
      },
    }
  }

  toEncodable() {
    return {
      Named: {
        bool_field: this.value.boolField,
        u8_field: this.value.u8Field,
        nested: types.BarStruct.toEncodable(this.value.nested),
      },
    }
  }
}

export type StructFields = [types.BarStructFields]
export type StructValue = [types.BarStruct]

export interface StructJSON {
  kind: "Struct"
  value: [types.BarStructJSON]
}

export class Struct {
  readonly discriminator = 3
  readonly kind = "Struct"
  readonly value: StructValue

  constructor(value: StructFields) {
    this.value = [new types.BarStruct({ ...value[0] })]
  }

  toJSON(): StructJSON {
    return {
      kind: "Struct",
      value: [this.value[0].toJSON()],
    }
  }

  toEncodable() {
    return {
      Struct: {
        _0: types.BarStruct.toEncodable(this.value[0]),
      },
    }
  }
}

export type OptionStructFields = [types.BarStructFields | null]
export type OptionStructValue = [types.BarStruct | null]

export interface OptionStructJSON {
  kind: "OptionStruct"
  value: [types.BarStructJSON | null]
}

export class OptionStruct {
  readonly discriminator = 4
  readonly kind = "OptionStruct"
  readonly value: OptionStructValue

  constructor(value: OptionStructFields) {
    this.value = [(value[0] && new types.BarStruct({ ...value[0] })) || null]
  }

  toJSON(): OptionStructJSON {
    return {
      kind: "OptionStruct",
      value: [(this.value[0] && this.value[0].toJSON()) || null],
    }
  }

  toEncodable() {
    return {
      OptionStruct: {
        _0:
          (this.value[0] && types.BarStruct.toEncodable(this.value[0])) || null,
      },
    }
  }
}

export type VecStructFields = [Array<types.BarStructFields>]
export type VecStructValue = [Array<types.BarStruct>]

export interface VecStructJSON {
  kind: "VecStruct"
  value: [Array<types.BarStructJSON>]
}

export class VecStruct {
  readonly discriminator = 5
  readonly kind = "VecStruct"
  readonly value: VecStructValue

  constructor(value: VecStructFields) {
    this.value = [value[0].map((item) => new types.BarStruct({ ...item }))]
  }

  toJSON(): VecStructJSON {
    return {
      kind: "VecStruct",
      value: [this.value[0].map((item) => item.toJSON())],
    }
  }

  toEncodable() {
    return {
      VecStruct: {
        _0: this.value[0].map((item) => types.BarStruct.toEncodable(item)),
      },
    }
  }
}

export interface NoFieldsJSON {
  kind: "NoFields"
}

export class NoFields {
  readonly discriminator = 6
  readonly kind = "NoFields"

  toJSON(): NoFieldsJSON {
    return {
      kind: "NoFields",
    }
  }

  toEncodable() {
    return {
      NoFields: {},
    }
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function fromDecoded(obj: any): types.FooEnumKind {
  if (typeof obj !== "object") {
    throw new Error("Invalid enum object")
  }

  if ("Unnamed" in obj) {
    const val = obj["Unnamed"]
    return new Unnamed([
      val["_0"],
      val["_1"],
      types.BarStruct.fromDecoded(val["_2"]),
    ])
  }
  if ("UnnamedSingle" in obj) {
    const val = obj["UnnamedSingle"]
    return new UnnamedSingle([types.BarStruct.fromDecoded(val["_0"])])
  }
  if ("Named" in obj) {
    const val = obj["Named"]
    return new Named({
      boolField: val["bool_field"],
      u8Field: val["u8_field"],
      nested: types.BarStruct.fromDecoded(val["nested"]),
    })
  }
  if ("Struct" in obj) {
    const val = obj["Struct"]
    return new Struct([types.BarStruct.fromDecoded(val["_0"])])
  }
  if ("OptionStruct" in obj) {
    const val = obj["OptionStruct"]
    return new OptionStruct([
      (val["_0"] && types.BarStruct.fromDecoded(val["_0"])) || null,
    ])
  }
  if ("VecStruct" in obj) {
    const val = obj["VecStruct"]
    return new VecStruct([
      val["_0"].map((item) => types.BarStruct.fromDecoded(item)),
    ])
  }
  if ("NoFields" in obj) {
    return new NoFields()
  }

  throw new Error("Invalid enum object")
}

export function fromJSON(obj: types.FooEnumJSON): types.FooEnumKind {
  switch (obj.kind) {
    case "Unnamed": {
      return new Unnamed([
        obj.value[0],
        obj.value[1],
        types.BarStruct.fromJSON(obj.value[2]),
      ])
    }
    case "UnnamedSingle": {
      return new UnnamedSingle([types.BarStruct.fromJSON(obj.value[0])])
    }
    case "Named": {
      return new Named({
        boolField: obj.value.boolField,
        u8Field: obj.value.u8Field,
        nested: types.BarStruct.fromJSON(obj.value.nested),
      })
    }
    case "Struct": {
      return new Struct([types.BarStruct.fromJSON(obj.value[0])])
    }
    case "OptionStruct": {
      return new OptionStruct([
        (obj.value[0] && types.BarStruct.fromJSON(obj.value[0])) || null,
      ])
    }
    case "VecStruct": {
      return new VecStruct([
        obj.value[0].map((item) => types.BarStruct.fromJSON(item)),
      ])
    }
    case "NoFields": {
      return new NoFields()
    }
  }
}

export function layout(property?: string) {
  const ret = borsh.rustEnum([
    borsh.struct(
      [borsh.bool("_0"), borsh.u8("_1"), types.BarStruct.layout("_2")],
      "Unnamed"
    ),
    borsh.struct([types.BarStruct.layout("_0")], "UnnamedSingle"),
    borsh.struct(
      [
        borsh.bool("bool_field"),
        borsh.u8("u8_field"),
        types.BarStruct.layout("nested"),
      ],
      "Named"
    ),
    borsh.struct([types.BarStruct.layout("_0")], "Struct"),
    borsh.struct(
      [borsh.option(types.BarStruct.layout(), "_0")],
      "OptionStruct"
    ),
    borsh.struct([borsh.vec(types.BarStruct.layout(), "_0")], "VecStruct"),
    borsh.struct([], "NoFields"),
  ])
  if (property !== undefined) {
    return ret.replicate(property)
  }
  return ret
}
