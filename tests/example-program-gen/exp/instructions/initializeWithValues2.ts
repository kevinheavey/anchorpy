import { TransactionInstruction, PublicKey } from "@solana/web3.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import BN from "bn.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as borsh from "@project-serum/borsh" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as types from "../types" // eslint-disable-line @typescript-eslint/no-unused-vars
import { PROGRAM_ID } from "../programId"

export interface InitializeWithValues2Args {
  vecOfOption: Array<BN | null>
}

export interface InitializeWithValues2Accounts {
  state: PublicKey
  payer: PublicKey
  systemProgram: PublicKey
}

export const layout = borsh.struct([
  borsh.vec(borsh.option(borsh.u64()), "vecOfOption"),
])

export function initializeWithValues2(
  args: InitializeWithValues2Args,
  accounts: InitializeWithValues2Accounts
) {
  const keys = [
    { pubkey: accounts.state, isSigner: true, isWritable: true },
    { pubkey: accounts.payer, isSigner: true, isWritable: true },
    { pubkey: accounts.systemProgram, isSigner: false, isWritable: false },
  ]
  const identifier = Buffer.from([248, 190, 21, 97, 239, 148, 39, 181])
  const buffer = Buffer.alloc(1000)
  const len = layout.encode(
    {
      vecOfOption: args.vecOfOption,
    },
    buffer
  )
  const data = Buffer.concat([identifier, buffer]).slice(0, 8 + len)
  const ix = new TransactionInstruction({ keys, programId: PROGRAM_ID, data })
  return ix
}
