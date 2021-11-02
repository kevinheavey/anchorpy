# Changelog

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
