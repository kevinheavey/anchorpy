# Tutorial


!!! note
    It is recommended to use the generated client instead of the dynamic client where possible, as it is easier to
    work with and comes with proper type hints.

This tutorial takes the JS snippets from the official Anchor tutorial
and shows how to achieve the same thing using AnchorPy.

## [A Minimal Example](https://project-serum.github.io/anchor/tutorials/tutorial-0.html)
This section covers the `basic-0` tutorial:
### [Generating a Client](https://project-serum.github.io/anchor/tutorials/tutorial-0.html#generating-a-client)
Here is how we generate a client from an IDL and use it to interact with a smart contract.


=== "Python"
    ````python
    from pathlib import Path
    import asyncio
    import json
    from solders.pubkey import Pubkey
    from anchorpy import Idl, Program

    async def main():
        # Read the generated IDL.
        with Path("target/idl/basic_0.json").open() as f:
            raw_idl = f.read()
        idl = Idl.from_json(raw_idl)
        # Address of the deployed program.
        program_id = Pubkey.from_string("<YOUR-PROGRAM-ID>")
        # Generate the program client from IDL.
        async with Program(idl, program_id) as program:
            # Execute the RPC.
            await program.rpc["initialize"]()
        # If we don't use the context manager, we need to
        # close the underlying http client, otherwise we get warnings.
        # await program.close()

    asyncio.run(main())

    ````

=== "JS"
    ````javascript
    // Read the generated IDL.
    const idl = JSON.parse(require('fs').readFileSync('./target/idl/basic_0.json', 'utf8'));

    // Address of the deployed program.
    const programId = new anchor.web3.Pubkey('<YOUR-PROGRAM-ID>');

    // Generate the program client from IDL.
    const program = new anchor.Program(idl, programId);

    // Execute the RPC.
    await program.rpc.initialize();

    ````

Note the differences between Python and JS here:

- We call `program.rpc["initialize"]()` instead of `program.rpc.initialize()`
- We call `program.close()` to close the HTTP connection.

### [Workspaces](https://project-serum.github.io/anchor/tutorials/tutorial-0.html#workspaces)

Here is how workspaces look in AnchorPy:


=== "Python"
    ````python
    import asyncio
    from anchorpy import create_workspace, close_workspace

    async def main():
        # Read the deployed program from the workspace.
        workspace = create_workspace()
        program = workspace["basic_0"]
        # Execute the RPC.
        await program.rpc["initialize"]()
        # Close all HTTP clients in the workspace, otherwise we get warnings.
        await close_workspace(workspace)
    
    asyncio.run(main())

    ````

=== "JS"
    ````javascript
    // Read the deployed program from the workspace.
    const program = anchor.workspace.Basic0;

    // Execute the RPC.
    await program.rpc.initialize();

    ````

Note the differences between Python and JS:

- Workspace instantiation is explicit: we have to call the `create_workspace` function.
    - Note however that AnchorPy provides the `workspace_fixture` factory for convenience.
      See the [testing](../testing/index.md) section for more.
- We have a `close_workspace` function that calls `close_program` on all the programs
in the workspace.
- The workspace is called `basic_0` instead of `Basic0`. This is because AnchorPy uses snake case 🐍
!!! Note
    AnchorPy uses the same case convention as Rust, so names should look just like they do in `lib.rs`.
    If you're unsure of a name, check `program.idl`: it shows how AnchorPy sees the IDL after parsing
    it and converting some cases.

## [Arguments and Accounts](https://project-serum.github.io/anchor/tutorials/tutorial-1.html)
### [Creating and Initializing Accounts](https://project-serum.github.io/anchor/tutorials/tutorial-1.html#creating-and-initializing-accounts)

Here is how we call an RPC function with arguments.
As in the main Anchor tutorial, we will use `anchor/tutorial/examples/basic-1`:

=== "Python"
    ````python
    import asyncio
    from solders.keypair import Keypair
    from solders.system_program import ID as SYS_PROGRAM_ID
    from anchorpy import create_workspace, close_workspace, Context

    async def main():
        # Read the deployed program from the workspace.
        workspace = create_workspace()
        # The program to execute.
        program = workspace["basic_1"]
        # The Account to create.
        my_account = Keypair()
        # Execute the RPC.
        accounts = {
            "my_account": my_account.pubkey(),
            "user": program.provider.wallet.public_key,
            "system_program": SYS_PROGRAM_ID
        }
        await program.rpc["initialize"](1234, ctx=Context(accounts=accounts, signers=[my_account]))
        # Close all HTTP clients in the workspace, otherwise we get warnings.
        await close_workspace(workspace)
    
    asyncio.run(main())

    ````

=== "JS"
    ````javascript
    // The program to execute.
    const program = anchor.workspace.Basic1;

    // The Account to create.
    const myAccount = anchor.web3.Keypair();

    // Create the new account and initialize it with the program.
    await program.rpc.initialize(new anchor.BN(1234), {
    accounts: {
        myAccount: myAccount.Pubkey,
        user: provider.wallet.Pubkey,
        systemProgram: SystemProgram.programId,
    },
    signers: [myAccount],
    });

    ````

Note how AnchorPy uses an explicit `Context` object in contrast to TS/JS.
