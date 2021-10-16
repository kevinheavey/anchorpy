# Tutorial

This tutorial takes the JS snippets from the official Anchor tutorial
and shows how to achieve the same thing using AnchorPy.
## [A Minimal Example](https://project-serum.github.io/anchor/tutorials/tutorial-0.html)

### [Generating a Client](https://project-serum.github.io/anchor/tutorials/tutorial-0.html#generating-a-client)

Differences between Python and JS here:

- We call `program.rpc["initialize"]()` instead of `program.rpc.initialize()`
- We call `program.close()` to close the HTTP connection.

=== "Python"
    ````python
    from pathlib import Path
    import asyncio
    import json
    from solana.publickey import PublicKey
    from anchorpy import Idl, Program

    async def main():
        # Read the generated IDL.
        with Path("target/idl/basic_0.json").open() as f:
            raw_idl = json.load(f)
        idl = Idl.from_json(raw_idl)
        # Address of the deployed program.
        program_id = PublicKey("<YOUR-PROGRAM-ID>")
        # Generate the program client from IDL.
        program = Program(idl, program_id)
        # Execute the RPC.
        await program.rpc["initialize"]()
        # Close the underlying http client, otherwise we get warnings.
        await program.close()

    asyncio.run(main())

    ````

=== "JS"
    ````javascript
    // Read the generated IDL.
    const idl = JSON.parse(require('fs').readFileSync('./target/idl/basic_0.json', 'utf8'));

    // Address of the deployed program.
    const programId = new anchor.web3.PublicKey('<YOUR-PROGRAM-ID>');

    // Generate the program client from IDL.
    const program = new anchor.Program(idl, programId);

    // Execute the RPC.
    await program.rpc.initialize();

    ````

### [Workspaces](https://project-serum.github.io/anchor/tutorials/tutorial-0.html#workspaces)

Differences between Python and JS:

- Workspace instantiation is explicit: we have to call the `create_workspace` function.
- We have a `close_workspace` function that calls `close_program` on all the programs
in the workspace.
- The workspace is called `basic_0` instead of `Basic0`. This is because AnchorPy doesn't
convert names to camelcase.
    - Note however that AnchorPy also doesn't convert names to snakecase. If you're not
    sure how to spell a name, check the IDL - AnchorPy spelling will always match the IDL.

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