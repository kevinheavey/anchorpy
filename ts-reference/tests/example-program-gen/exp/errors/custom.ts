export type CustomError = SomeError | OtherError

export class SomeError extends Error {
  readonly code = 6000
  readonly name = "SomeError"
  readonly msg = "Example error."

  constructor() {
    super("6000: Example error.")
  }
}

export class OtherError extends Error {
  readonly code = 6001
  readonly name = "OtherError"
  readonly msg = "Another error."

  constructor() {
    super("6001: Another error.")
  }
}

export function fromCode(code: number): CustomError | null {
  switch (code) {
    case 6000:
      return new SomeError()
    case 6001:
      return new OtherError()
  }

  return null
}
