# Changelog

## [0.4.2] - 2021-11-20

### Fixed

- Upgrade solana-py dep so `.send` returns the tx signature and not the signature status.
- Dedupe transaction signers
## [0.4.1] - 2021-11-20

### Fixed

- Missing `pytest-xprocess` dep (it was marked as a dev dependency only)

## [0.4.0] - 2021-11-20

### Changed

- BREAKING: Some program namespace entries are now snake-case (https://github.com/kevinheavey/anchorpy/pull/13).
This affects `program.rpc`, `program.instruction`, fields inside `program.type` entries, and 
the `accounts` argument to `Context`.
- BREAKING: `instructions` is replaced with `pre_instructions` and `post_instructions`. (https://github.com/kevinheavey/anchorpy/pull/18)
- BREAKING: User-defined types must now be constructed using the new `program.type` namespace. https://github.com/kevinheavey/anchorpy/pull/7 This also affects the return type of `.fetch` - the returned object is now a dataclass and requires `.` access instead of `[]`.
- BREAKING: `provider.client` is renamed to `provider.connection`.
- Refactor `.send` to use more `solana-py` functionality. https://github.com/kevinheavey/anchorpy/pull/11

### Added

- Added a Pytest plugin for a better testing experience https://github.com/kevinheavey/anchorpy/pull/5 https://github.com/kevinheavey/anchorpy/pull/17
- Added support for fetching multiple accounts at once https://github.com/kevinheavey/anchorpy/pull/19


## [0.3.0] - 2021-11-02

### Added

- Add `at` and `fetch_idl` classmethods to `Program`.
- Better error message when an incorrect number of arguments is passed to an RPC function.
- Allow for `state` when parsing the IDL.
- Add support for filtering `.all()` with a buffer, like in the TS client.
- Add missing `.accounts` utility method to `InstructionFn`.
- Add `py.typed` file for mypy support.
- Add `utils.rpc.invoke` function.

### Fixed

- Fix missing async/await keywords in `simulate.py`.
- Catch unhandled TypeError when looking for custom error code in RPC response.

## [0.2.0] - 2021-10-18

### Added

- `associated_address` function in `utils/token.py`

### Fixed

- Fixed errors with non-string IDL types.
## [0.1.1] - 2021-10-16

Add optional `path` and `url` parameters to `create_workspace`.
This is so we can overhaul the tests.
## [0.1.0] - 2021-10-16

First release 🚀
