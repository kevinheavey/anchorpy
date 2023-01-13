# Client Generator

The `anchorpy client-gen` command generates a Python client based on an Anchor IDL. This client provides functions for
generating instructions and class definitions for fetching and serializing accounts. The output is very similar
to the Typescript code produced by [anchor-client-gen](https://github.com/kklas/anchor-client-gen).

## Features

- Fully typed.
- Supports all Anchor field types.
- Makes enums and complex types easy to work with.
- Generates error classes for each error.
- Provides `to_json` and `from_json` utility functions for types and accounts.

!!! note
    It is recommended to use the generated client instead of the dynamic client where possible, as it is easier to
    work with and comes with proper type hints.

## Usage

```console
$ anchorpy client-gen --help
Usage: anchorpy client-gen [OPTIONS] IDL OUT

  Generate Python client code from the specified anchor IDL.

Arguments:
  IDL  Anchor IDL file path  [required]
  OUT  Output directory.  [required]

Options:
  --program-id TEXT  Optional program ID to be included in the code
  --help             Show this message and exit.

```

## Example

<div class="termy">

```console
$ anchorpy client-gen path/to/idl.json ./my_client
generating package...
generating program_id.py...
generating errors.py...
generating instructions...
generating types...
generating accounts...
```

</div>

This will generate code to `./my_client`:

```
.
├── accounts
│   ├── foo_account.py
│   └── __init__.py
├── instructions
│   ├── some_instruction.py
│   ├── other_instruction.py
│   └── __init__.py
├── types
│   ├── bar_struct.py
│   ├── baz_enum.py
│   └── __init__.py
├── errors
│   ├── anchor.py
│   ├── custom.py
│   └── __init__.py
└── program_id.py
```

## Using the generated client

### Instructions

```python
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from anchorpy import Provider
from my_client.instructions import some_instruction

 # call an instruction
foo_account = Keypair()

ix = some_instruction({
  "foo_param": "...",
  "bar_param": "...",
  ...
}, {
  "foo_account": foo_account.pubkey(), # signer
  "bar_account": Pubkey("..."),
  ...
})
tx = Transaction().add(ix)

provider = Provider.local()

await provider.send(tx, [payer, foo_account])
```

### Accounts

```python
from solders.pubkey import Pubkey
from my_client.accounts import FooAccount

# fetch an account
addr = Pubkey("...")

acc = await FooAccount.fetch(connection, addr)
if acc is None:
    # the fetch method returns null when the account is uninitialized
    raise ValueError("account not found")


# convert to a JSON object
obj = acc.to_json()
print(obj)

# load from JSON
acc_from_json = FooAccount.from_json(obj)
```

### Types

```python
# structs

from my_client.types import BarStruct

bar_struct = BarStruct(
  some_field="...",
  other_field="...",
)

print(bar_struct.to_json())
```

```python
# enums

from my_client.types import baz_enum

tuple_enum = baz_enum.SomeTupleKind((True, False, "some value"))
struct_enum = baz_enum.SomeStructKind({
  "field1": "...",
  "field2": "...",
})
disc_enum = baz_enum.SomeDiscriminantKind()

print(tuple_enum.toJSON(), struct_enum.toJSON(), disc_enum.toJSON())
```

```python
# types are used as arguments in instruction calls (where needed):
ix = some_instruction({
  "some_struct_field": bar_struct,
  "some_enum_field": tuple_enum,
  # ...
}, {
  # accounts
  # ...
})

# in case of struct fields, it's also possible to pass them as objects:
ix = some_instruction({
  "some_struct_field": {
    "some_field": "...",
    "other_field": "...",
  },
  # ...,
}, {
  # accounts
  # ...
})
```

### Errors

```python
from solana.rpc.core import RPCException
from my_client.errors import from_tx_error
from my_client.errors.custom import SomeCustomError

try:
  await provider.send(tx, [payer])
except RPCException as exc:
    parsed = from_tx_error(exc)
    raise parsed from exc
```

## Program ID

The client generator pulls the program ID from:

- the input IDL
- the `--program-id` flag

If the IDL doesn't contain the program ID then you will need to pass it via the `--program-id` flag.

This program ID is then written into the `program_id.py` file.

