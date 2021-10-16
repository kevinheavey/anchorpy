# A note on tests

For now, most of the test files here need to be copied into their corresponding folder in the Anchor repo to be run.
For example, `test_basic_0.py` needs to be copied into `anchor/examples/tutorial/basic-0/tests`, and then the Anchor.toml
must be changed so that the `scripts` section looks like this:

```toml
[scripts]
test = "pytest"

```

Then the test can be run with `anchor test`.
