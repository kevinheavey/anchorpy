export type AnchorError =
  | InstructionMissing
  | InstructionFallbackNotFound
  | InstructionDidNotDeserialize
  | InstructionDidNotSerialize
  | IdlInstructionStub
  | IdlInstructionInvalidProgram
  | ConstraintMut
  | ConstraintHasOne
  | ConstraintSigner
  | ConstraintRaw
  | ConstraintOwner
  | ConstraintRentExempt
  | ConstraintSeeds
  | ConstraintExecutable
  | ConstraintState
  | ConstraintAssociated
  | ConstraintAssociatedInit
  | ConstraintClose
  | ConstraintAddress
  | ConstraintZero
  | ConstraintTokenMint
  | ConstraintTokenOwner
  | ConstraintMintMintAuthority
  | ConstraintMintFreezeAuthority
  | ConstraintMintDecimals
  | ConstraintSpace
  | RequireViolated
  | RequireEqViolated
  | RequireKeysEqViolated
  | RequireNeqViolated
  | RequireKeysNeqViolated
  | RequireGtViolated
  | RequireGteViolated
  | AccountDiscriminatorAlreadySet
  | AccountDiscriminatorNotFound
  | AccountDiscriminatorMismatch
  | AccountDidNotDeserialize
  | AccountDidNotSerialize
  | AccountNotEnoughKeys
  | AccountNotMutable
  | AccountOwnedByWrongProgram
  | InvalidProgramId
  | InvalidProgramExecutable
  | AccountNotSigner
  | AccountNotSystemOwned
  | AccountNotInitialized
  | AccountNotProgramData
  | AccountNotAssociatedTokenAccount
  | AccountSysvarMismatch
  | StateInvalidAddress
  | DeclaredProgramIdMismatch
  | Deprecated

export class InstructionMissing extends Error {
  readonly code = 100
  readonly name = "InstructionMissing"
  readonly msg = "8 byte instruction identifier not provided"

  constructor() {
    super("100: 8 byte instruction identifier not provided")
  }
}

export class InstructionFallbackNotFound extends Error {
  readonly code = 101
  readonly name = "InstructionFallbackNotFound"
  readonly msg = "Fallback functions are not supported"

  constructor() {
    super("101: Fallback functions are not supported")
  }
}

export class InstructionDidNotDeserialize extends Error {
  readonly code = 102
  readonly name = "InstructionDidNotDeserialize"
  readonly msg = "The program could not deserialize the given instruction"

  constructor() {
    super("102: The program could not deserialize the given instruction")
  }
}

export class InstructionDidNotSerialize extends Error {
  readonly code = 103
  readonly name = "InstructionDidNotSerialize"
  readonly msg = "The program could not serialize the given instruction"

  constructor() {
    super("103: The program could not serialize the given instruction")
  }
}

export class IdlInstructionStub extends Error {
  readonly code = 1000
  readonly name = "IdlInstructionStub"
  readonly msg = "The program was compiled without idl instructions"

  constructor() {
    super("1000: The program was compiled without idl instructions")
  }
}

export class IdlInstructionInvalidProgram extends Error {
  readonly code = 1001
  readonly name = "IdlInstructionInvalidProgram"
  readonly msg =
    "The transaction was given an invalid program for the IDL instruction"

  constructor() {
    super(
      "1001: The transaction was given an invalid program for the IDL instruction"
    )
  }
}

export class ConstraintMut extends Error {
  readonly code = 2000
  readonly name = "ConstraintMut"
  readonly msg = "A mut constraint was violated"

  constructor() {
    super("2000: A mut constraint was violated")
  }
}

export class ConstraintHasOne extends Error {
  readonly code = 2001
  readonly name = "ConstraintHasOne"
  readonly msg = "A has_one constraint was violated"

  constructor() {
    super("2001: A has_one constraint was violated")
  }
}

export class ConstraintSigner extends Error {
  readonly code = 2002
  readonly name = "ConstraintSigner"
  readonly msg = "A signer constraint was violated"

  constructor() {
    super("2002: A signer constraint was violated")
  }
}

export class ConstraintRaw extends Error {
  readonly code = 2003
  readonly name = "ConstraintRaw"
  readonly msg = "A raw constraint was violated"

  constructor() {
    super("2003: A raw constraint was violated")
  }
}

export class ConstraintOwner extends Error {
  readonly code = 2004
  readonly name = "ConstraintOwner"
  readonly msg = "An owner constraint was violated"

  constructor() {
    super("2004: An owner constraint was violated")
  }
}

export class ConstraintRentExempt extends Error {
  readonly code = 2005
  readonly name = "ConstraintRentExempt"
  readonly msg = "A rent exemption constraint was violated"

  constructor() {
    super("2005: A rent exemption constraint was violated")
  }
}

export class ConstraintSeeds extends Error {
  readonly code = 2006
  readonly name = "ConstraintSeeds"
  readonly msg = "A seeds constraint was violated"

  constructor() {
    super("2006: A seeds constraint was violated")
  }
}

export class ConstraintExecutable extends Error {
  readonly code = 2007
  readonly name = "ConstraintExecutable"
  readonly msg = "An executable constraint was violated"

  constructor() {
    super("2007: An executable constraint was violated")
  }
}

export class ConstraintState extends Error {
  readonly code = 2008
  readonly name = "ConstraintState"
  readonly msg = "A state constraint was violated"

  constructor() {
    super("2008: A state constraint was violated")
  }
}

export class ConstraintAssociated extends Error {
  readonly code = 2009
  readonly name = "ConstraintAssociated"
  readonly msg = "An associated constraint was violated"

  constructor() {
    super("2009: An associated constraint was violated")
  }
}

export class ConstraintAssociatedInit extends Error {
  readonly code = 2010
  readonly name = "ConstraintAssociatedInit"
  readonly msg = "An associated init constraint was violated"

  constructor() {
    super("2010: An associated init constraint was violated")
  }
}

export class ConstraintClose extends Error {
  readonly code = 2011
  readonly name = "ConstraintClose"
  readonly msg = "A close constraint was violated"

  constructor() {
    super("2011: A close constraint was violated")
  }
}

export class ConstraintAddress extends Error {
  readonly code = 2012
  readonly name = "ConstraintAddress"
  readonly msg = "An address constraint was violated"

  constructor() {
    super("2012: An address constraint was violated")
  }
}

export class ConstraintZero extends Error {
  readonly code = 2013
  readonly name = "ConstraintZero"
  readonly msg = "Expected zero account discriminant"

  constructor() {
    super("2013: Expected zero account discriminant")
  }
}

export class ConstraintTokenMint extends Error {
  readonly code = 2014
  readonly name = "ConstraintTokenMint"
  readonly msg = "A token mint constraint was violated"

  constructor() {
    super("2014: A token mint constraint was violated")
  }
}

export class ConstraintTokenOwner extends Error {
  readonly code = 2015
  readonly name = "ConstraintTokenOwner"
  readonly msg = "A token owner constraint was violated"

  constructor() {
    super("2015: A token owner constraint was violated")
  }
}

export class ConstraintMintMintAuthority extends Error {
  readonly code = 2016
  readonly name = "ConstraintMintMintAuthority"
  readonly msg = "A mint mint authority constraint was violated"

  constructor() {
    super("2016: A mint mint authority constraint was violated")
  }
}

export class ConstraintMintFreezeAuthority extends Error {
  readonly code = 2017
  readonly name = "ConstraintMintFreezeAuthority"
  readonly msg = "A mint freeze authority constraint was violated"

  constructor() {
    super("2017: A mint freeze authority constraint was violated")
  }
}

export class ConstraintMintDecimals extends Error {
  readonly code = 2018
  readonly name = "ConstraintMintDecimals"
  readonly msg = "A mint decimals constraint was violated"

  constructor() {
    super("2018: A mint decimals constraint was violated")
  }
}

export class ConstraintSpace extends Error {
  readonly code = 2019
  readonly name = "ConstraintSpace"
  readonly msg = "A space constraint was violated"

  constructor() {
    super("2019: A space constraint was violated")
  }
}

export class RequireViolated extends Error {
  readonly code = 2500
  readonly name = "RequireViolated"
  readonly msg = "A require expression was violated"

  constructor() {
    super("2500: A require expression was violated")
  }
}

export class RequireEqViolated extends Error {
  readonly code = 2501
  readonly name = "RequireEqViolated"
  readonly msg = "A require_eq expression was violated"

  constructor() {
    super("2501: A require_eq expression was violated")
  }
}

export class RequireKeysEqViolated extends Error {
  readonly code = 2502
  readonly name = "RequireKeysEqViolated"
  readonly msg = "A require_keys_eq expression was violated"

  constructor() {
    super("2502: A require_keys_eq expression was violated")
  }
}

export class RequireNeqViolated extends Error {
  readonly code = 2503
  readonly name = "RequireNeqViolated"
  readonly msg = "A require_neq expression was violated"

  constructor() {
    super("2503: A require_neq expression was violated")
  }
}

export class RequireKeysNeqViolated extends Error {
  readonly code = 2504
  readonly name = "RequireKeysNeqViolated"
  readonly msg = "A require_keys_neq expression was violated"

  constructor() {
    super("2504: A require_keys_neq expression was violated")
  }
}

export class RequireGtViolated extends Error {
  readonly code = 2505
  readonly name = "RequireGtViolated"
  readonly msg = "A require_gt expression was violated"

  constructor() {
    super("2505: A require_gt expression was violated")
  }
}

export class RequireGteViolated extends Error {
  readonly code = 2506
  readonly name = "RequireGteViolated"
  readonly msg = "A require_gte expression was violated"

  constructor() {
    super("2506: A require_gte expression was violated")
  }
}

export class AccountDiscriminatorAlreadySet extends Error {
  readonly code = 3000
  readonly name = "AccountDiscriminatorAlreadySet"
  readonly msg = "The account discriminator was already set on this account"

  constructor() {
    super("3000: The account discriminator was already set on this account")
  }
}

export class AccountDiscriminatorNotFound extends Error {
  readonly code = 3001
  readonly name = "AccountDiscriminatorNotFound"
  readonly msg = "No 8 byte discriminator was found on the account"

  constructor() {
    super("3001: No 8 byte discriminator was found on the account")
  }
}

export class AccountDiscriminatorMismatch extends Error {
  readonly code = 3002
  readonly name = "AccountDiscriminatorMismatch"
  readonly msg = "8 byte discriminator did not match what was expected"

  constructor() {
    super("3002: 8 byte discriminator did not match what was expected")
  }
}

export class AccountDidNotDeserialize extends Error {
  readonly code = 3003
  readonly name = "AccountDidNotDeserialize"
  readonly msg = "Failed to deserialize the account"

  constructor() {
    super("3003: Failed to deserialize the account")
  }
}

export class AccountDidNotSerialize extends Error {
  readonly code = 3004
  readonly name = "AccountDidNotSerialize"
  readonly msg = "Failed to serialize the account"

  constructor() {
    super("3004: Failed to serialize the account")
  }
}

export class AccountNotEnoughKeys extends Error {
  readonly code = 3005
  readonly name = "AccountNotEnoughKeys"
  readonly msg = "Not enough account keys given to the instruction"

  constructor() {
    super("3005: Not enough account keys given to the instruction")
  }
}

export class AccountNotMutable extends Error {
  readonly code = 3006
  readonly name = "AccountNotMutable"
  readonly msg = "The given account is not mutable"

  constructor() {
    super("3006: The given account is not mutable")
  }
}

export class AccountOwnedByWrongProgram extends Error {
  readonly code = 3007
  readonly name = "AccountOwnedByWrongProgram"
  readonly msg =
    "The given account is owned by a different program than expected"

  constructor() {
    super(
      "3007: The given account is owned by a different program than expected"
    )
  }
}

export class InvalidProgramId extends Error {
  readonly code = 3008
  readonly name = "InvalidProgramId"
  readonly msg = "Program ID was not as expected"

  constructor() {
    super("3008: Program ID was not as expected")
  }
}

export class InvalidProgramExecutable extends Error {
  readonly code = 3009
  readonly name = "InvalidProgramExecutable"
  readonly msg = "Program account is not executable"

  constructor() {
    super("3009: Program account is not executable")
  }
}

export class AccountNotSigner extends Error {
  readonly code = 3010
  readonly name = "AccountNotSigner"
  readonly msg = "The given account did not sign"

  constructor() {
    super("3010: The given account did not sign")
  }
}

export class AccountNotSystemOwned extends Error {
  readonly code = 3011
  readonly name = "AccountNotSystemOwned"
  readonly msg = "The given account is not owned by the system program"

  constructor() {
    super("3011: The given account is not owned by the system program")
  }
}

export class AccountNotInitialized extends Error {
  readonly code = 3012
  readonly name = "AccountNotInitialized"
  readonly msg = "The program expected this account to be already initialized"

  constructor() {
    super("3012: The program expected this account to be already initialized")
  }
}

export class AccountNotProgramData extends Error {
  readonly code = 3013
  readonly name = "AccountNotProgramData"
  readonly msg = "The given account is not a program data account"

  constructor() {
    super("3013: The given account is not a program data account")
  }
}

export class AccountNotAssociatedTokenAccount extends Error {
  readonly code = 3014
  readonly name = "AccountNotAssociatedTokenAccount"
  readonly msg = "The given account is not the associated token account"

  constructor() {
    super("3014: The given account is not the associated token account")
  }
}

export class AccountSysvarMismatch extends Error {
  readonly code = 3015
  readonly name = "AccountSysvarMismatch"
  readonly msg = "The given public key does not match the required sysvar"

  constructor() {
    super("3015: The given public key does not match the required sysvar")
  }
}

export class StateInvalidAddress extends Error {
  readonly code = 4000
  readonly name = "StateInvalidAddress"
  readonly msg = "The given state account does not have the correct address"

  constructor() {
    super("4000: The given state account does not have the correct address")
  }
}

export class DeclaredProgramIdMismatch extends Error {
  readonly code = 4100
  readonly name = "DeclaredProgramIdMismatch"
  readonly msg = "The declared program id does not match the actual program id"

  constructor() {
    super("4100: The declared program id does not match the actual program id")
  }
}

export class Deprecated extends Error {
  readonly code = 5000
  readonly name = "Deprecated"
  readonly msg = "The API being used is deprecated and should no longer be used"

  constructor() {
    super("5000: The API being used is deprecated and should no longer be used")
  }
}

export function fromCode(code: number): AnchorError | null {
  switch (code) {
    case 100:
      return new InstructionMissing()
    case 101:
      return new InstructionFallbackNotFound()
    case 102:
      return new InstructionDidNotDeserialize()
    case 103:
      return new InstructionDidNotSerialize()
    case 1000:
      return new IdlInstructionStub()
    case 1001:
      return new IdlInstructionInvalidProgram()
    case 2000:
      return new ConstraintMut()
    case 2001:
      return new ConstraintHasOne()
    case 2002:
      return new ConstraintSigner()
    case 2003:
      return new ConstraintRaw()
    case 2004:
      return new ConstraintOwner()
    case 2005:
      return new ConstraintRentExempt()
    case 2006:
      return new ConstraintSeeds()
    case 2007:
      return new ConstraintExecutable()
    case 2008:
      return new ConstraintState()
    case 2009:
      return new ConstraintAssociated()
    case 2010:
      return new ConstraintAssociatedInit()
    case 2011:
      return new ConstraintClose()
    case 2012:
      return new ConstraintAddress()
    case 2013:
      return new ConstraintZero()
    case 2014:
      return new ConstraintTokenMint()
    case 2015:
      return new ConstraintTokenOwner()
    case 2016:
      return new ConstraintMintMintAuthority()
    case 2017:
      return new ConstraintMintFreezeAuthority()
    case 2018:
      return new ConstraintMintDecimals()
    case 2019:
      return new ConstraintSpace()
    case 2500:
      return new RequireViolated()
    case 2501:
      return new RequireEqViolated()
    case 2502:
      return new RequireKeysEqViolated()
    case 2503:
      return new RequireNeqViolated()
    case 2504:
      return new RequireKeysNeqViolated()
    case 2505:
      return new RequireGtViolated()
    case 2506:
      return new RequireGteViolated()
    case 3000:
      return new AccountDiscriminatorAlreadySet()
    case 3001:
      return new AccountDiscriminatorNotFound()
    case 3002:
      return new AccountDiscriminatorMismatch()
    case 3003:
      return new AccountDidNotDeserialize()
    case 3004:
      return new AccountDidNotSerialize()
    case 3005:
      return new AccountNotEnoughKeys()
    case 3006:
      return new AccountNotMutable()
    case 3007:
      return new AccountOwnedByWrongProgram()
    case 3008:
      return new InvalidProgramId()
    case 3009:
      return new InvalidProgramExecutable()
    case 3010:
      return new AccountNotSigner()
    case 3011:
      return new AccountNotSystemOwned()
    case 3012:
      return new AccountNotInitialized()
    case 3013:
      return new AccountNotProgramData()
    case 3014:
      return new AccountNotAssociatedTokenAccount()
    case 3015:
      return new AccountSysvarMismatch()
    case 4000:
      return new StateInvalidAddress()
    case 4100:
      return new DeclaredProgramIdMismatch()
    case 5000:
      return new Deprecated()
  }

  return null
}
