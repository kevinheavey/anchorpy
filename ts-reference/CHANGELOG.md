# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v0.24.0]

### Features

- Add fetchMultiple method to generated account classes (#4)
- Anchor errors are now also generated and parsed ([#25](https://github.com/kklas/anchor-client-gen/pull/25))

### Fixes

- Don't generate instruction, account, and type index files when they don't exist [b5c3009](https://github.com/kklas/anchor-client-gen/commit/b5c3009ae03ca1b26792d27e9290f9e9235880e2)
- Fixed field value generation for some nested types [1c3a355](https://github.com/kklas/anchor-client-gen/commit/1c3a35552aaae8e318a29e3faf2b4c5df5cc0229)
- Fixed parsing of errors coming from CPI calls ([#25](https://github.com/kklas/anchor-client-gen/pull/25))

### Breaking

- Location of custom error classes has been changed from `errors` to `errors/custom` ([#25](https://github.com/kklas/anchor-client-gen/pull/25))
