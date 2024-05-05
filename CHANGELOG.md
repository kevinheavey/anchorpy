# Changelog

## [0.20.1] - 2024-05-05

### Changed

- Relax solana-py dependency [#(141)](https://github.com/kevinheavey/anchorpy/pull/141)


## [0.20.0] - 2024-03-29

### Changed

- Use solana-py 0.33.0 [#(138)](https://github.com/kevinheavey/anchorpy/pull/138)

## [0.19.1] - 2024-02-12

### Fixed

- Fix anchorpy import when no extras are included [#(136)](https://github.com/kevinheavey/anchorpy/pull/136)

## [0.19.0] - 2024-02-12

### Added

- Add support for alias types in IDL [#(129)](https://github.com/kevinheavey/anchorpy/pull/129)

### Changed

- Make the Pytest plugin dependencies optional. Install with `pip install anchorpy[pytest]` if you 
want the Pytest plugin [#(129)](https://github.com/kevinheavey/anchorpy/pull/129)
- Update to Anchor 0.29.0 [#(132)](https://github.com/kevinheavey/anchorpy/pull/132)
- Update to solders 0.20.0 [#(132)](https://github.com/kevinheavey/anchorpy/pull/132)
- Update to solana-py 0.32.0 [#(132)](https://github.com/kevinheavey/anchorpy/pull/132)

## [0.18.0] - 2023-07-20

### Changed

Client-gen: add support for optional accounts [#(128)](https://github.com/kevinheavey/anchorpy/pull/128)

### Fixed

Client-gen: fix missing sanitization in to_json method generation [#(129)](https://github.com/kevinheavey/anchorpy/pull/129)

## [0.17.2] - 2023-06-02

### Changed

Use latest `solders` and `solana-py` [#(126)](https://github.com/kevinheavey/anchorpy/pull/126)

## [0.17.1] - 2023-05-14

### Changed

Use latest `solders` and `solana-py` [#(125)](https://github.com/kevinheavey/anchorpy/pull/125)

## [0.17.0] - 2023-05-06

### Added

- Add `bankrun_fixture` to `anchorpy.pytest_plugin`. This calls
[`solders.bankrun.start()`](https://kevinheavey.github.io/solders/examples/bankrun.html)
and deploys programs to the test environment.

### Changed

- Use latest solders and solana-py.
- Don't do any signing or blockhash fetching in `Provider.send`, `.send_all` and `.simulate`.
- Remove `SendTxRequest` class
- Replace `Transaction` with `VersionedTransaction` in the `.transaction` namespace.
- Add mandatory `payer` and `blockhash` params to `.transaction` so it always returns a fully-formed tx.

## [0.16.0] - 2023-02-23

### Changed

Bump minimum version of zstandard dep [#(112)](https://github.com/kevinheavey/anchorpy/pull/112)

## [0.15.0] - 2023-01-13

### Changed

Use latest solana-py [#(111)](https://github.com/kevinheavey/anchorpy/pull/111)

## [0.14.0] - 2022-12-16

### Changed

Use latest solana-py [#(106)](https://github.com/kevinheavey/anchorpy/pull/106)

## [0.13.1] - 2022-11-23

### Changed

- Update pytest dependencies [#(101)](https://github.com/kevinheavey/anchorpy/pull/101)

## [0.13.0] - 2022-11-22

### Added

- Add PDA resolution and common pubkeys to client-gen [#(97)](https://github.com/kevinheavey/anchorpy/pull/97)
- Add support for non-Anchor clients, starting with SPL Token [(#98)](https://github.com/kevinheavey/anchorpy/pull/98)
- Add methods builder [(#99)](https://github.com/kevinheavey/anchorpy/pull/99)

## [0.12.0] - 2022-11-01

### Changed

- Use Rust (via [anchorpy-core](https://github.com/kevinheavey/anchorpy-core)) to parse IDLs.
This removes the `anchorpy.idl.Idl` class and replaces it with `anchorpy_core.idl.Idl`,
which uses some different types and supports newer IDL features.
This change only affects code that used the Idl class directly; normal AnchorPy behaviour is unchanged. 

## [0.11.0] - 2022-10-15

### Changed

- Use latest solana-py [#(92)](https://github.com/kevinheavey/anchorpy/pull/92)

### Fixed

- Remove vestigial sumtypes dep [#(91)](https://github.com/kevinheavey/anchorpy/pull/91)

## [0.10.0] - 2022-08-11

### Added

- Added support for docs in IDLs [#(88)](https://github.com/kevinheavey/anchorpy/pull/88)
- Add first-class support for `remaining_accounts` [#(83)](https://github.com/kevinheavey/anchorpy/pull/83)
- Allow dynamically overriding `program_id` [#(83)](https://github.com/kevinheavey/anchorpy/pull/83)

### Fixed

- Fix identifiers clashing with Python keywords [#(87)](https://github.com/kevinheavey/anchorpy/pull/87)

## [0.9.4] - 2022-07-18

### Fixed

Add missing BorshPubkey import in generated client types [#(81)](https://github.com/kevinheavey/anchorpy/pull/81)

## [0.9.3] - 2022-07-06

### Changed

Use latest `solana-py` [#(78)](https://github.com/kevinheavey/anchorpy/pull/78)

## [0.9.2] - 2022-06-02

### Fixed

- Handle empty structs in clientgen [#(75)](https://github.com/kevinheavey/anchorpy/pull/75)

## [0.9.1] - 2022-05-19

### Fixed

- Fixed edge case where invalid `import` code gets generated [#(71)](https://github.com/kevinheavey/anchorpy/pull/71)
- Include logs in ProgramError instances [#(72)](https://github.com/kevinheavey/anchorpy/pull/72)

## [0.9.0] - 2022-05-03

### Added

- Added `anchorpy client-gen` [(#70)](https://github.com/kevinheavey/anchorpy/pull/70)
- Added floats support to IDL [(#70)](https://github.com/kevinheavey/anchorpy/pull/70)

## [0.8.3] - 2022-04-29

### Changed

- Updated error codes [(#69)](https://github.com/kevinheavey/anchorpy/pull/69)
- Updated event parser to support sol_log_data [(#68)](https://github.com/kevinheavey/anchorpy/pull/68)
- Updated solana-py dependency to 0.23.1 [(#67)](https://github.com/kevinheavey/anchorpy/pull/67)

## [0.8.2] - 2022-04-15

### Added

- Update IDL types [(#64)](https://github.com/kevinheavey/anchorpy/pull/64) and [(#66)](https://github.com/kevinheavey/anchorpy/pull/66)

## [0.8.1] - 2022-03-16

### Changed

Upgraded zstandard dependency [(#60)](https://github.com/kevinheavey/anchorpy/pull/60)

## [0.8.0] - 2022-03-09

### Added

- `Provider.readonly` constructor for using AnchorPy only to fetch data
  [(#58)](https://github.com/kevinheavey/anchorpy/pull/58)
- `commitment` parameter in `.fetch` and `.fetch_multiple` methods
  [(#58)](https://github.com/kevinheavey/anchorpy/pull/58)

### Fixed

- Cache some generated Python types to avoid issues with checking equality
  [(#57)](https://github.com/kevinheavey/anchorpy/pull/57)

## [0.7.0] - 2022-02-07

### Changed

- Add experimental support for tuple enum variants

### Fixed

- Don't crash when loading a Program that uses unsupported types

## [0.6.5] - 2022-01-28

### Changed

Update pytest and pytest-asyncio dependencies.

## [0.6.4] - 2022-01-22

### Changed

Update ipython dependency to pick up ACE vulnerability patch. [More here.](https://www.reddit.com/r/Python/comments/s9l5oy/arbitrary_code_execution_vulnerability_discovered/)

## [0.6.3] - 2022-01-21

### Fixed

Some more deps needed upating.

## [0.6.2] - 2022-01-21

### Fixed

Release again because last release was made before merging.

## [0.6.1] - 2022-01-21

### Changed

- Use `pyheck` instead of `inflection` for case conversion
- Update `solana` and `apischema` dependencies.

## [0.6.0] - 2021-12-21

### Added

Added AnchorPy CLI ([#42](https://github.com/kevinheavey/anchorpy/pull/42)).

### Changed

Bumped `apischema` dependency to latest version ([#42](https://github.com/kevinheavey/anchorpy/pull/42)).

## [0.5.0] - 2021-12-18

### Changed

- AnchorPy now targets Anchor 0.19.0 ([#39](https://github.com/kevinheavey/anchorpy/pull/39))

## [0.4.6] - 2021-12-13

### Fixed

- Fixed event parser ([#38](https://github.com/kevinheavey/anchorpy/pull/38))

## [0.4.5] - 2021-12-06

- Support `solana-py` 0.19.0.

## [0.4.4] - 2021-12-02

### Fixed

- Update `sumtypes` dep so it works on Python 3.10
- Fix handling of enums with C-like struct variants.

## [0.4.3] - 2021-11-22

### Added

- `Program.fetch_raw_idl` method to fetch an IDL json without parsing it into an `Idl` instance.

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
