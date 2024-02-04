# AnchorPy
<div align="center">
    <img src="https://raw.githubusercontent.com/kevinheavey/anchorpy/main/docs/img/logo.png" width="40%" height="40%">
</div>

---

[![Discord Chat](https://img.shields.io/discord/889577356681945098?color=blueviolet)](https://discord.gg/sxy4zxBckh)  

AnchorPy is the gateway to interacting with [Anchor](https://github.com/project-serum/anchor) programs in Python.
It provides:

- A static client generator
- A dynamic client similar to `anchor-ts`
- A Pytest plugin
- A CLI with various utilities for Anchor Python development.

Read the [Documentation](https://kevinheavey.github.io/anchorpy/).



## Installation (requires Python >=3.9)

```sh
pip install anchorpy[cli, pytest]

```
Or, if you're not using the CLI or Pytest plugin features of AnchorPy you can just run `pip install anchorpy`.

### Development Setup

If you want to contribute to AnchorPy, follow these steps to get set up:

1. Install [poetry](https://python-poetry.org/docs/#installation)
2. Install dev dependencies:
```sh
poetry install

```
3. Activate the poetry shell:
```sh
poetry shell

```
