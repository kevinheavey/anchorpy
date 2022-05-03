# Comparison with Typescript

While AnchorPy is quite similar to the Anchor Typescript client,
there are some differences:

## Dictionaries instead of objects

AnchorPy tends to use dictionaries, so it uses `[key]` in some places where
`anchor-ts` would use `.key`.
For example, AnchorPy uses `workspace["basic_1"]` instead of `workspace.basic_1`,
and `program.rpc["initialize"]()` instead of `program.rpc.initialize()`

## Explicit `Context` object

AnchorPy uses a `Context` dataclass and has a `ctx` keyword argument when
calling `.rpc` functions, whereas Typescript is a bit less structured.

We call `program.rpc["my_func"](ctx=Context({"my_account": my_account}))`
instead of `program.rpc["my_func"]({"my_account": my_account})`

## snake_case 🐍 instead of camelCase 🐪

AnchorPy uses more `snake_case` to match Rust and be Pythonic.
Specifically, the following names are snake-case in AnchorPy:

- Workspaces: `workspace["puppet_master"]` instead of `workspace["puppetMaster"]`
- Instructions: `program.rpc["my_func"]` (and `program.instruction["my_func"]`) instead of 
`program.rpc["myFunc"]`.
- Accounts in the `ctx` arg: `{"my_account": my_account}` instead of `{"myAccount": my_account}`
- Fields in user-defined types: `program.type["TransactionAccount"](is_writable=True)` instead of
`program.type["TransactionAccount"](isWritable=True)`

## `program.type` namespace for user-defined types

The AnchorPy `Program` object has a `.type` attribute for instantiating user-defined types. This is not present in
the Typescript client. See the [examples](examples.md) for more on this.
