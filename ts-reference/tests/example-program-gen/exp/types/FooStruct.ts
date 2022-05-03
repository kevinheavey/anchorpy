import { PublicKey } from "@solana/web3.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import BN from "bn.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as types from "../types" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as borsh from "@project-serum/borsh"

export interface FooStructFields {
  field1: number
  field2: number
  nested: types.BarStructFields
  vecNested: Array<types.BarStructFields>
  optionNested: types.BarStructFields | null
  enumField: types.FooEnumKind
}

export interface FooStructJSON {
  field1: number
  field2: number
  nested: types.BarStructJSON
  vecNested: Array<types.BarStructJSON>
  optionNested: types.BarStructJSON | null
  enumField: types.FooEnumJSON
}

export class FooStruct {
  readonly field1: number
  readonly field2: number
  readonly nested: types.BarStruct
  readonly vecNested: Array<types.BarStruct>
  readonly optionNested: types.BarStruct | null
  readonly enumField: types.FooEnumKind

  constructor(fields: FooStructFields) {
    this.field1 = fields.field1
    this.field2 = fields.field2
    this.nested = new types.BarStruct({ ...fields.nested })
    this.vecNested = fields.vecNested.map(
      (item) => new types.BarStruct({ ...item })
    )
    this.optionNested =
      (fields.optionNested &&
        new types.BarStruct({ ...fields.optionNested })) ||
      null
    this.enumField = fields.enumField
  }

  static layout(property?: string) {
    return borsh.struct(
      [
        borsh.u8("field1"),
        borsh.u16("field2"),
        types.BarStruct.layout("nested"),
        borsh.vec(types.BarStruct.layout(), "vecNested"),
        borsh.option(types.BarStruct.layout(), "optionNested"),
        types.FooEnum.layout("enumField"),
      ],
      property
    )
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  static fromDecoded(obj: any) {
    return new FooStruct({
      field1: obj.field1,
      field2: obj.field2,
      nested: types.BarStruct.fromDecoded(obj.nested),
      vecNested: obj.vecNested.map((item) => types.BarStruct.fromDecoded(item)),
      optionNested:
        (obj.optionNested && types.BarStruct.fromDecoded(obj.optionNested)) ||
        null,
      enumField: types.FooEnum.fromDecoded(obj.enumField),
    })
  }

  static toEncodable(fields: FooStructFields) {
    return {
      field1: fields.field1,
      field2: fields.field2,
      nested: types.BarStruct.toEncodable(fields.nested),
      vecNested: fields.vecNested.map((item) =>
        types.BarStruct.toEncodable(item)
      ),
      optionNested:
        (fields.optionNested &&
          types.BarStruct.toEncodable(fields.optionNested)) ||
        null,
      enumField: fields.enumField.toEncodable(),
    }
  }

  toJSON(): FooStructJSON {
    return {
      field1: this.field1,
      field2: this.field2,
      nested: this.nested.toJSON(),
      vecNested: this.vecNested.map((item) => item.toJSON()),
      optionNested: (this.optionNested && this.optionNested.toJSON()) || null,
      enumField: this.enumField.toJSON(),
    }
  }

  static fromJSON(obj: FooStructJSON): FooStruct {
    return new FooStruct({
      field1: obj.field1,
      field2: obj.field2,
      nested: types.BarStruct.fromJSON(obj.nested),
      vecNested: obj.vecNested.map((item) => types.BarStruct.fromJSON(item)),
      optionNested:
        (obj.optionNested && types.BarStruct.fromJSON(obj.optionNested)) ||
        null,
      enumField: types.FooEnum.fromJSON(obj.enumField),
    })
  }

  toEncodable() {
    return FooStruct.toEncodable(this)
  }
}
