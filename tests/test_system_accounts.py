# """Mimics anchor/tests/system-accounts."""
# from pathlib import Path
# from typing import AsyncGenerator
# from dataclasses import dataclass

# from pytest import mark, fixture, raises
# from solana.keypair import Keypair
# from spl.token.constants import TOKEN_PROGRAM_ID
# from spl.token.async_client import AsyncToken

# from anchorpy import Program, create_workspace, close_workspace, Context, Provider
# from anchorpy.pytest_plugin import get_localnet
# from anchorpy.error import ProgramError

# PATH = Path("anchor/tests/system-accounts")

# localnet = get_localnet(PATH)


# @dataclass
# class Initialize:
#     authority: Keypair
#     wallet: Keypair


# @fixture(scope="module")
# async def program(localnet) -> AsyncGenerator[Program, None]:
#     """Create a Program instance."""
#     workspace = create_workspace(PATH)
#     yield workspace["token_proxy"]
#     await close_workspace(workspace)


# @fixture(scope="module")
# async def provider(program: Program) -> Provider:
#     """Get a Provider instance."""
#     return program.provider


# @fixture(scope="module")
# async def initialize(program: Program, provider: Provider) -> Initialize:
#     authority = provider.wallet.payer
#     wallet = Keypair()
#     tx = await program.rpc["initialize"](
#         ctx=Context(
#             accounts={"authority": authority.public_key, "wallet": wallet.public_key},
#             signers=[authority],
#         )
#     )
#     print(f"Your transaction signature: {tx}")
#     return Initialize(authority, wallet)


# @mark.asyncio
# async def test_error(
#     initialize: Initialize, program: Program, provider: Provider
# ) -> None:
#     mint = await AsyncToken.create_mint(
#         provider.client,
#         initialize.authority,
#         initialize.authority.public_key,
#         9,
#         TOKEN_PROGRAM_ID,
#     )
#     token_account = await mint.create_associated_token_account(
#         initialize.wallet.public_key
#     )
#     await mint.mint_to(
#         token_account,
#         initialize.authority.public_key,
#         1000000000,
#         opts=provider.opts,
#     )
#     with raises(ProgramError) as excinfo:
#         await program.rpc["initialize"](
#             ctx=Context(
#                 accounts={
#                     "authority": initialize.authority.public_key,
#                     "wallet": token_account,
#                 },
#                 signers=[initialize.authority],
#             )
#         )
#     assert excinfo.value.msg == "The given account is not owned by the system program"
#     assert excinfo.value.code == 171
