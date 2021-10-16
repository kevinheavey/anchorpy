# Testing with AnchorPy

Anchor lets you run whatever tests you want using the `[scripts]` section of `Anchor.toml`.
This means we can write integration tests in Python instead of JS.

If you want to try this for yourself, clone the main Anchor repo and
copy [test_basic_1.py](https://github.com/kevinheavey/anchorpy/blob/main/tests/test_basic_1.py)
into `anchor/examples/tutorial/basic-1/tests/`, and change the `scripts` section of `Anchor.toml`
to look like this:

```toml
[scripts]
test = "pytest"

```

Then run `anchor test` and voila!.

!!! note
    You must have `pytest-asyncio` installed for `test_basic_1.py` to work.
