from anchorpy.workspace import create_workspace

workspace = create_workspace()
program = workspace["basic_0"]
res = program.rpc["initialize"]()
print(res)
print("DONE!!!")
