# AnchorPy CLI

AnchorPy comes with a CLI to make your life easier when using Python with Anchor.


```console
$ anchorpy --help
Usage: anchorpy [OPTIONS] COMMAND [ARGS]...

  AnchorPy CLI.

Options:
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

Commands:
  init   Create a basic Python test file for an Anchor program.
  shell  Start IPython shell with AnchorPy workspace object initialized.
```

## Commands

### Init

```console
$ anchorpy init --help
Usage: anchorpy init [OPTIONS] PROGRAM_NAME

  Create a basic Python test file for an Anchor program.

  This does not replace `anchor init`, but rather should be run after it.

  The test file will live at `tests/test_$PROGRAM_NAME.py`.

Arguments:
  PROGRAM_NAME  The name of the Anchor program.  [required]

Options:
  --help  Show this message and exit.
```

### Shell

```console
$ anchorpy shell --help
Usage: anchorpy shell [OPTIONS]

  Start IPython shell with AnchorPy workspace object initialized.

  Note that you should run `anchor localnet` before `anchorpy shell`.

Options:
  --help  Show this message and exit.
```

#### Example

<div class="termy">

```console
$ cd anchor/examples/tutorial/basic-0 && anchorpy shell
Python 3.9.1 (default, Dec 11 2020, 14:32:07)
Type 'copyright', 'credits' or 'license' for more information
IPython 7.30.1 -- An enhanced Interactive Python. Type '?' for help.

Hint: type `workspace` to see the Anchor workspace object.

# In [1]:$ await workspace["basic_0"].rpc["initialize"]()
Out[1]: '2q1Z8BcsSBikMLEFoeFGhUukfsNYLJx7y33rMZ57Eh4gAHJxpJ9oP9b9aFyrizh9wcuiVtAAxvmBifCXdqWeNLor'
```

</div>

### Client-gen

See [Client Generator](../clientgen)