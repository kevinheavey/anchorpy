# Introduction
<div align="center">
    <img src="https://raw.githubusercontent.com/kevinheavey/anchorpy/main/docs/img/logo.png" width="40%" height="40%">
</div>

---
AnchorPy is the gateway to interacting with [Anchor](https://github.com/project-serum/anchor) programs in Python.
It provides:

- A [static client generator](clientgen)
- A [dynamic client](dynamic_client) similar to `anchor-ts`
- A [Pytest plugin](testing/#1-pytest-plugin)
- A [CLI](cli) with various utilities for Anchor Python development.

## Installation (requires Python >= 3.9)

```shell
pip install anchorpy[cli, pytest]
```

Or, if you're not using the CLI or Pytest plugin features of AnchorPy you can just run `pip install anchorpy`.

!!! note
    These docs will assume you've read the [Anchor documentation](https://www.anchor-lang.com/) first.
