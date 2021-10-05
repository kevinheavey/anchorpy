import json
import os

from solana.account import Account
from solana.rpc import types
from solana.rpc.commitment import Single
from solana.system_program import create_account, CreateAccountParams, SYS_PROGRAM_ID
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.transaction import Transaction

from anchorpy.program import Program
from anchorpy.provider import Provider, LocalWallet
from anchorpy.idl import Idl


def get_provider() -> Provider:
    return Provider(
        "http://localhost:8899",
        LocalWallet.local(),
        types.TxOpts(skip_confirmation=False, preflight_commitment=Single),
    )


def load_program(fpath: str) -> Program:
    with open(fpath, "r") as f:
        idl = Idl.from_json(json.load(f))
    assert idl.metadata is not None
    return Program(idl, idl.metadata.address, get_provider())


def test_basic_0():
    basic0 = load_program(
        os.path.expanduser(
            "~/l/anchor/examples/tutorial/basic-0/target/idl/basic_0.json"
        )
    )
    result = basic0.rpc.initialize()


def test_basic_1():
    program = load_program(
        os.path.expanduser(
            "~/l/anchor/examples/tutorial/basic-1/target/idl/basic_1.json"
        )
    )
    print(f"[TEST] basic-1: {program.program_id}")

    # Creates and initializes an account in two different transactions
    my_account = Account()
    tx = Transaction()
    tx.add(
        create_account(
            CreateAccountParams(
                from_pubkey=program.provider.wallet.public_key,
                new_account_pubkey=my_account.public_key(),
                space=8 + 8,
                lamports=program.provider.client.get_minimum_balance_for_rent_exemption(
                    8 + 8
                )["result"],
                program_id=program.program_id,
            )
        )
    )
    program.provider.send(tx, [my_account])

    program.rpc.initialize(
        1234,
        {
            "accounts": {
                "myAccount": my_account.public_key(),
                "rent": SYSVAR_RENT_PUBKEY,
            }
        },
    )

    account = program.account.myAccount.fetch(my_account.public_key())
    assert account.data == 1234

    # Creates and initializes an account in a single atomic transaction
    my_account = Account()
    program.rpc.initialize(
        1234,
        {
            "accounts": {
                "myAccount": my_account.public_key(),
                "rent": SYSVAR_RENT_PUBKEY,
            },
            "signers": [my_account],
            "instructions": [
                create_account(
                    CreateAccountParams(
                        from_pubkey=program.provider.wallet.public_key,
                        new_account_pubkey=my_account.public_key(),
                        space=8 + 8,
                        lamports=program.provider.client.get_minimum_balance_for_rent_exemption(
                            8 + 8
                        )[
                            "result"
                        ],
                        program_id=program.program_id,
                    )
                )
            ],
        },
    )

    account = program.account.myAccount.fetch(my_account.public_key())
    assert account.data == 1234

    # Creates and initializes an account in a single atomic transaction (simplified)
    my_account = Account()
    program.rpc.initialize(
        1234,
        {
            "accounts": {
                "myAccount": my_account.public_key(),
                "rent": SYSVAR_RENT_PUBKEY,
            },
            "signers": [my_account],
            "instructions": [program.account.myAccount.create_instruction(my_account)],
        },
    )
    account = program.account.myAccount.fetch(my_account.public_key())
    assert account.data == 1234

    # Updates a previously created account
    program.rpc.update(4321, {"accounts": {"myAccount": my_account.public_key()}})

    account = program.account.myAccount.fetch(my_account.public_key())
    assert account.data == 4321

    print("[PASS]")


def test_basic_2():
    program = load_program(
        os.path.expanduser(
            "~/l/anchor/examples/tutorial/basic-2/target/idl/basic_2.json"
        )
    )
    print(f"[TEST] basic-2: {program.program_id}")
    counter = Account()

    # Creates a counter
    program.rpc.create(
        program.provider.wallet.public_key,
        {
            "accounts": {"counter": counter.public_key(), "rent": SYSVAR_RENT_PUBKEY},
            "signers": [counter],
            "instructions": [program.account.counter.create_instruction(counter)],
        },
    )
    counter_account = program.account.counter.fetch(counter.public_key())
    assert counter_account.authority == program.provider.wallet.public_key
    assert counter_account.count == 0

    # Updates a counter
    program.rpc.increment(
        {
            "accounts": {
                "counter": counter.public_key(),
                "authority": program.provider.wallet.public_key,
            }
        }
    )
    counter_account = program.account.counter.fetch(counter.public_key())
    assert counter_account.authority == program.provider.wallet.public_key
    assert counter_account.count == 1


def test_basic_3():
    puppet = load_program(
        os.path.expanduser(
            "~/l/anchor/examples/tutorial/basic-3/target/idl/puppet.json"
        )
    )
    puppet_master = load_program(
        os.path.expanduser(
            "~/l/anchor/examples/tutorial/basic-3/target/idl/puppet_master.json"
        )
    )
    print(f"[TEST] basic-3: {puppet.program_id=}, {puppet_master.program_id=}")

    # Performs CPI from puppet master to puppet
    puppet_account = Account()
    puppet.rpc.initialize(
        {
            "accounts": {
                "puppet": puppet_account.public_key(),
                "rent": SYSVAR_RENT_PUBKEY,
            },
            "signers": [puppet_account],
            "instructions": [puppet.account.puppet.create_instruction(puppet_account)],
        }
    )

    puppet_master.rpc.pullStrings(
        111,
        {
            "accounts": {
                "puppet": puppet_account.public_key(),
                "puppetProgram": puppet.program_id,
            }
        },
    )

    puppet_account = puppet.account.puppet.fetch(puppet_account.public_key())
    assert puppet_account.data == 111


def test_basic_5():
    program = load_program(
        os.path.expanduser(
            "~/l/anchor/examples/tutorial/basic-5/target/idl/basic_5.json"
        )
    )
    mint = Account()

    # Sets up the test
    program.rpc.createMint(
        {
            "accounts": {"mint": mint.public_key(), "rent": SYSVAR_RENT_PUBKEY},
            "instructions": [program.account.mint.create_instruction(mint)],
            "signers": [mint],
        }
    )

    # Creates an associated token account
    authority = program.provider.wallet.public_key
    associated_token = program.account.token.associated_address(
        authority, mint.public_key()
    )
    program.rpc.createToken(
        {
            "accounts": {
                "token": associated_token,
                "authority": authority,
                "mint": mint.public_key(),
                "rent": SYSVAR_RENT_PUBKEY,
                "systemProgram": SYS_PROGRAM_ID,
            }
        }
    )

    account = program.account.token.associated(authority, mint.public_key())
    assert account.amount == 0
    assert account.authority == authority
    assert account.mint == mint.public_key()


def main():
    pass
    # test_basic_0()
    # test_basic_1()
    # test_basic_2()
    # test_basic_4()
    # test_basic_5()


if __name__ == "__main__":
    main()
