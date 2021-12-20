from IPython import embed
from anchorpy import create_workspace
from subprocess import Popen


def start_shell():
    x = 1
    y = 2
    buzz = 10
    workspace = create_workspace("anchor/examples/tutorial/basic-0")
    embed(colors="neutral", using="asyncio")


start_shell()
