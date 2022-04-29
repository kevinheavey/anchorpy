import { TransactionInstruction, PublicKey } from "@solana/web3.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import BN from "bn.js" // eslint-disable-line @typescript-eslint/no-unused-vars
import * as borsh from "@project-serum/borsh" // eslint-disable-line @typescript-eslint/no-unused-vars
import { PROGRAM_ID } from "../programId"

export interface CreateArgs {
  authority: PublicKey
}

export interface CreateAccounts {
  counter: PublicKey
  user: PublicKey
  systemProgram: PublicKey
}

export const layout = borsh.struct([borsh.publicKey("authority")])

export function create(args: CreateArgs, accounts: CreateAccounts) {
  const keys = [
    { pubkey: accounts.counter, isSigner: true, isWritable: true },
    { pubkey: accounts.user, isSigner: true, isWritable: true },
    { pubkey: accounts.systemProgram, isSigner: false, isWritable: false },
  ]
  const identifier = Buffer.from([24, 30, 200, 40, 5, 28, 7, 119])
  const buffer = Buffer.alloc(1000)
  const len = layout.encode(
    {
      authority: args.authority,
    },
    buffer
  )
  const data = Buffer.concat([identifier, buffer]).slice(0, 8 + len)
  const ix = new TransactionInstruction({ keys, programId: PROGRAM_ID, data })
  return ix
}
