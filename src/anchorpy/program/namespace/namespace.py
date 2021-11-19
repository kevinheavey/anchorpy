"""This module deals with creating the program object's namespaces."""
from typing import Any, Dict, Tuple

from solana.publickey import PublicKey
from anchorpy.program.namespace.rpc import (
    RpcFn,
    build_rpc_item,
)

from anchorpy.coder.coder import Coder


from anchorpy.idl import Idl
from anchorpy.provider import Provider
