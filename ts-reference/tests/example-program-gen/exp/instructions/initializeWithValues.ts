import { TransactionInstruction, PublicKey } from "@solana/web3.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import BN from "bn.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as borsh from "@project-serum/borsh" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as types from "../types" // eslint-disable-line @typescript-eslint/no-unused-vars
import { PROGRAM_ID } from "../programId"

export interface InitializeWithValuesArgs {
  boolField: boolean
  u8Field: number
  i8Field: number
  u16Field: number
  i16Field: number
  u32Field: number
  i32Field: number
  f32Field: number
  u64Field: BN
  i64Field: BN
  f64Field: number
  u128Field: BN
  i128Field: BN
  bytesField: Array<number>
  stringField: string
  pubkeyField: PublicKey
  vecField: Array<BN>
  vecStructField: Array<types.FooStructFields>
  optionField: boolean | null
  optionStructField: types.FooStructFields | null
  structField: types.FooStructFields
  arrayField: Array<boolean>
  enumField1: types.FooEnumKind
  enumField2: types.FooEnumKind
  enumField3: types.FooEnumKind
  enumField4: types.FooEnumKind
}

export interface InitializeWithValuesAccounts {
  state: PublicKey
  nested: {
    clock: PublicKey
    rent: PublicKey
  }
  payer: PublicKey
  systemProgram: PublicKey
}

export const layout = borsh.struct([
  borsh.bool("boolField"),
  borsh.u8("u8Field"),
  borsh.i8("i8Field"),
  borsh.u16("u16Field"),
  borsh.i16("i16Field"),
  borsh.u32("u32Field"),
  borsh.i32("i32Field"),
  borsh.f32("f32Field"),
  borsh.u64("u64Field"),
  borsh.i64("i64Field"),
  borsh.f64("f64Field"),
  borsh.u128("u128Field"),
  borsh.i128("i128Field"),
  borsh.vecU8("bytesField"),
  borsh.str("stringField"),
  borsh.publicKey("pubkeyField"),
  borsh.vec(borsh.u64(), "vecField"),
  borsh.vec(types.FooStruct.layout(), "vecStructField"),
  borsh.option(borsh.bool(), "optionField"),
  borsh.option(types.FooStruct.layout(), "optionStructField"),
  types.FooStruct.layout("structField"),
  borsh.array(borsh.bool(), 3, "arrayField"),
  types.FooEnum.layout("enumField1"),
  types.FooEnum.layout("enumField2"),
  types.FooEnum.layout("enumField3"),
  types.FooEnum.layout("enumField4"),
])

export function initializeWithValues(
  args: InitializeWithValuesArgs,
  accounts: InitializeWithValuesAccounts
) {
  const keys = [
    { pubkey: accounts.state, isSigner: true, isWritable: true },
    { pubkey: accounts.nested.clock, isSigner: false, isWritable: false },
    { pubkey: accounts.nested.rent, isSigner: false, isWritable: false },
    { pubkey: accounts.payer, isSigner: true, isWritable: true },
    { pubkey: accounts.systemProgram, isSigner: false, isWritable: false },
  ]
  const identifier = Buffer.from([220, 73, 8, 213, 178, 69, 181, 141])
  const buffer = Buffer.alloc(1000)
  const len = layout.encode(
    {
      boolField: args.boolField,
      u8Field: args.u8Field,
      i8Field: args.i8Field,
      u16Field: args.u16Field,
      i16Field: args.i16Field,
      u32Field: args.u32Field,
      i32Field: args.i32Field,
      f32Field: args.f32Field,
      u64Field: args.u64Field,
      i64Field: args.i64Field,
      f64Field: args.f64Field,
      u128Field: args.u128Field,
      i128Field: args.i128Field,
      bytesField: Buffer.from(args.bytesField),
      stringField: args.stringField,
      pubkeyField: args.pubkeyField,
      vecField: args.vecField,
      vecStructField: args.vecStructField.map((item) =>
        types.FooStruct.toEncodable(item)
      ),
      optionField: args.optionField,
      optionStructField:
        (args.optionStructField &&
          types.FooStruct.toEncodable(args.optionStructField)) ||
        null,
      structField: types.FooStruct.toEncodable(args.structField),
      arrayField: args.arrayField,
      enumField1: args.enumField1.toEncodable(),
      enumField2: args.enumField2.toEncodable(),
      enumField3: args.enumField3.toEncodable(),
      enumField4: args.enumField4.toEncodable(),
    },
    buffer
  )
  const data = Buffer.concat([identifier, buffer]).slice(0, 8 + len)
  const ix = new TransactionInstruction({ keys, programId: PROGRAM_ID, data })
  return ix
}
