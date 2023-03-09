# Examples

Here are some of the other things you can do with AnchorPy:

## Loading a Program from an on-chain IDL

If a program's IDL is stored on-chain, you can use it
to initialize a program object using `Program.at`.

````python
import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from anchorpy import Program, Provider, Wallet


async def main():
    client = AsyncClient("https://api.mainnet-beta.solana.com/")
    provider = Provider(client, Wallet.local())
    # load the Serum Swap Program (not the Serum dex itself).
    program_id = Pubkey.from_string("22Y43yTVxuUkoRKdm9thyRhQ3SdgQS7c7kB6UNCiaczD")
    program = await Program.at(
        program_id, provider
    )
    print(program.idl.name)  # swap
    await program.close()


asyncio.run(main())


````

## Instantiating user-defined types with `program.type`

### Enums

Suppose we have an instruction that expects an Enum called `Side`,
with variants `Buy` and `Sell`. The `Program` object has a `.type`
namespace to make it easy to use this enum:

````python
await program.rpc["my_func"](program.type["Side"].Buy())

````
See [test_token_proxy.py](https://github.com/kevinheavey/anchorpy/blob/main/tests/test_token_proxy.py)
for a more concrete example.

### Structs

`.type` also allows us to build structs defined in the IDL.
See this snippet from [test_multisig.py](https://github.com/kevinheavey/anchorpy/blob/main/tests/test_multisig.py):

````python
program.type["TransactionAccount"](
    pubkey=multisig.pubkey(),
    is_writable=True,
    is_signer=False,
)

````

## Bulk-fetching data with `.fetch_multiple`

You can use `.fetch_multiple` to get deserialized account data
for many accounts at once. Look at this example from `test_misc.py`:

````python
n_accounts = 200
pubkeys = [initialized_keypair.pubkey()] * n_accounts  # noqa: WPS435
data_accounts = await program.account["Data"].fetch_multiple(
    pubkeys, batch_size=2
)

````

The above example fetches data for the same pubkey 200 times which is
not very interesting, but it could just as easily be fetching 200
different accounts. The `.fetch_multiple` method uses async batch RPC requests
and `getMultipleAccounts` so it's quite efficient.

!!! warning
    Be mindful of your RPC provider when fetching data, and plan out how
    many requests you'll end up sending to the RPC node. You can reliably
    fetch around 300 public keys in one HTTP request.
