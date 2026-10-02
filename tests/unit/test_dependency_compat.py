"""Wire and RPC contracts across supported serialization dependencies."""
import base64
import json
import struct
from types import SimpleNamespace

import pytest
from anchorpy._compat import rpc_types
from anchorpy.borsh_extension import BorshPubkey, COption, EnumForCodegen
from anchorpy.error import ProgramError
from anchorpy.provider import Provider, Wallet
from anchorpy.utils.rpc import get_multiple_accounts
from anchorpy.utils.token import (
    create_token_account,
    parse_mint_account,
    parse_token_account,
)
from borsh_construct import U16, U64, CStruct
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.transaction import Transaction, VersionedTransaction
from solders.transaction_status import (
    InstructionErrorCustom,
    TransactionErrorInstructionError,
)
from spl.token.constants import TOKEN_PROGRAM_ID


@pytest.mark.parametrize(
    "status,limit,suffix",
    [
        ({"Idle": {}}, None, b"\x00\x00\x00\x00"),
        (
            {"Active": {"amount": 513}},
            0x1234,
            b"\x01\x01\x02\x00\x00\x00\x00\x00\x00\x01\x34\x12",
        ),
    ],
)
def test_borsh_extensions_preserve_wire_bytes(status, limit, suffix):
    layout = CStruct(
        "owner" / BorshPubkey,
        "status"
        / EnumForCodegen("Idle" / CStruct(), "Active" / CStruct("amount" / U64)),
        "limit" / COption(U16),
    )
    owner = Pubkey(bytes(range(32)))
    expected = bytes(range(32)) + suffix
    assert layout.build({"owner": owner, "status": status, "limit": limit}) == expected
    decoded = layout.parse(expected)
    assert decoded.owner == owner
    assert decoded.status == status
    assert decoded.limit == limit


def _request_json(body):
    # Older solana-py passes a solders request; newer releases pass a model.
    serialize = getattr(body, "to_json", None)
    return json.loads(serialize() if serialize else body.model_dump_json())


def test_program_error_preserves_custom_code_and_origin():
    program = Pubkey.new_unique()
    error = TransactionErrorInstructionError(0, InstructionErrorCustom(6000))
    logs = [f"Program {program} failed: custom program error: 0x1770"]
    parsed = ProgramError.parse_tx_error(error, {6000: "Rejected"}, program, logs)
    assert parsed is not None
    assert (parsed.code, parsed.msg, parsed.logs) == (6000, "Rejected", logs)
    assert ProgramError.parse_tx_error(error, {}, program, logs) is None
    assert ProgramError.parse_tx_error(error, {6000: "Rejected"}, program, []) is None
    assert (
        ProgramError.parse_tx_error(
            error, {6000: "Rejected"}, Pubkey.new_unique(), logs
        )
        is None
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("legacy", [True, False])
async def test_provider_simulates_original_signed_bytes(monkeypatch, legacy):
    payer = Keypair.from_seed(bytes([31]) * 32)
    transaction = (
        Transaction.new_signed_with_payer([], payer.pubkey(), [payer], Hash.default())
        if legacy
        else VersionedTransaction(
            MessageV0.try_compile(payer.pubkey(), [], [], Hash.default()), [payer]
        )
    )
    wire = bytes(transaction)
    observed = []

    async def request(body, parser):
        payload = _request_json(body)
        assert payload["method"] == "simulateTransaction"
        raw = base64.b64decode(payload["params"][0])
        assert raw == wire
        assert VersionedTransaction.from_bytes(raw).verify_with_results() == [True]
        assert payload["params"][1]["sigVerify"] is True
        assert payload["params"][1]["commitment"] == "confirmed"
        observed.append(payload)
        return parser.from_json(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "result": {
                        "context": {"slot": 1},
                        "value": {"err": None, "logs": []},
                    },
                }
            )
        )

    async with AsyncClient("http://localhost:8899") as client:
        monkeypatch.setattr(client._provider, "make_request", request)
        provider = Provider(
            client, Wallet(payer), rpc_types.TxOpts(preflight_commitment=Confirmed)
        )
        assert (await provider.simulate(transaction)).value.err is None
    assert len(observed) == 1
    assert bytes(transaction) == wire


@pytest.mark.asyncio
async def test_create_token_account_keeps_signers_and_confirmation(monkeypatch):
    payer = Keypair.from_seed(bytes([32]) * 32)
    mint = Pubkey.new_unique()
    owner = Pubkey.new_unique()
    sent = []
    methods = []
    rent = 2039280

    async def request(body, parser):
        payload = _request_json(body)
        method = payload["method"]
        methods.append(method)
        if method == "getMinimumBalanceForRentExemption":
            assert payload["params"][0] == 165
            result = rent
        elif method == "getLatestBlockhash":
            result = {
                "context": {"slot": 1},
                "value": {
                    "blockhash": str(Hash.default()),
                    "lastValidBlockHeight": 100,
                },
            }
        elif method == "sendTransaction":
            transaction = VersionedTransaction.from_bytes(
                base64.b64decode(payload["params"][0])
            )
            sent.append(transaction)
            assert payload["params"][1]["preflightCommitment"] == "confirmed"
            assert payload["params"][1]["skipPreflight"] is False
            result = str(transaction.signatures[0])
        elif method == "getSignatureStatuses":
            result = {
                "context": {"slot": 1},
                "value": [
                    {
                        "slot": 1,
                        "confirmations": None,
                        "err": None,
                        "status": {"Ok": None},
                        "confirmationStatus": "finalized",
                    }
                ],
            }
        else:
            raise AssertionError(f"unexpected RPC method: {method}")
        return parser.from_json(
            json.dumps({"jsonrpc": "2.0", "id": 0, "result": result})
        )

    async with AsyncClient("http://localhost:8899", commitment=Confirmed) as client:
        monkeypatch.setattr(client._provider, "make_request", request)
        account = await create_token_account(
            Provider(client, Wallet(payer)), mint, owner
        )
    assert len(sent) == 1
    transaction = sent[0]
    assert transaction.verify_with_results() == [True, True]
    assert list(transaction.message.account_keys[:2]) == [payer.pubkey(), account]
    create, initialize = transaction.message.instructions
    assert create.data == struct.pack("<IQQ", 0, rent, 165) + bytes(TOKEN_PROGRAM_ID)
    assert initialize.data == b"\x01"
    assert [transaction.message.account_keys[i] for i in initialize.accounts[:3]] == [
        account,
        mint,
        owner,
    ]
    assert "getSignatureStatuses" in methods


def test_token_account_and_mint_parsers_keep_tuple_contract():
    mint = Pubkey(bytes([7]) * 32)
    owner = Pubkey(bytes([8]) * 32)
    raw = (
        bytes(mint)
        + bytes(owner)
        + struct.pack("<QI", 513, 0)
        + bytes(32)
        + b"\x01"
        + struct.pack("<IQQI", 0, 0, 0, 0)
        + bytes(32)
    )
    account = parse_token_account(
        SimpleNamespace(value=SimpleNamespace(owner=TOKEN_PROGRAM_ID, data=raw))
    )
    assert isinstance(account, tuple)
    assert account[:3] == (mint, owner, 513)
    assert account.is_initialized is True
    raw_mint = (
        struct.pack("<I", 1)
        + bytes(owner)
        + struct.pack("<QBBI", 513, 6, 1, 0)
        + bytes(32)
    )
    info = parse_mint_account(
        SimpleNamespace(value=SimpleNamespace(owner=TOKEN_PROGRAM_ID, data=raw_mint))
    )
    assert isinstance(info, tuple)
    assert info == (owner, 513, 6, True, None)


@pytest.mark.asyncio
async def test_get_multiple_accounts_preserves_missing_slots(monkeypatch):
    first, missing, third = [Pubkey.new_unique() for _ in range(3)]
    owner = Pubkey.new_unique()

    async def post(url, *, content, headers):
        requests = json.loads(content)
        assert requests[0]["method"] == "getMultipleAccounts"
        assert requests[0]["params"][0] == [str(first), str(missing), str(third)]
        assert requests[0]["params"][1]["commitment"] == "confirmed"
        account = {
            "lamports": 1,
            "data": ["AQID", "base64"],
            "owner": str(owner),
            "executable": False,
            "rentEpoch": 0,
        }
        return SimpleNamespace(
            text=json.dumps(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 0,
                        "result": {
                            "context": {"slot": 1},
                            "value": [account, None, account],
                        },
                    }
                ]
            )
        )

    async with AsyncClient("http://localhost:8899", commitment=Confirmed) as client:
        monkeypatch.setattr(client._provider.session, "post", post)
        accounts = await get_multiple_accounts(client, [first, missing, third])
    assert accounts[0].pubkey == first
    assert accounts[0].account.data == b"\x01\x02\x03"
    assert accounts[1] is None
    assert accounts[2].pubkey == third
