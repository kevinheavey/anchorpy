import json

import pytest
from anchorpy import Coder
from anchorpy_idl import Idl


@pytest.mark.unit
def test_can_encode_and_decode_user_defined_types():
    """Test that the TypesCoder can encode and decode user-defined types."""
    idl_json = {
        "address": "Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS",
        "name": "basic_0",
        "metadata": {
          "name": "basic_0",
          "version": "0.1.0",
          "spec": "0.1.0",
          "description": "Created with Anchor"
        },
        "instructions": [
            {
                "name": "initialize",
                "accounts": [],
                "args": [],
                "discriminator": [],
            },
        ],
        "types": [
            {
                "name": "MintInfo",
                "type": {
                    "kind": "struct",
                    "fields": [
                        {
                            "name": "minted",
                            "type": "bool",
                        },
                        {
                            "name": "metadataUrl",
                            "type": "string",
                        },
                    ],
                },
            },
        ],
    }
    idl = Idl.from_json(json.dumps(idl_json))
    coder = Coder(idl)

    mint_info = {
        "minted": True,
        "metadata_url": "hello",
    }
    encoded = coder.types.encode("MintInfo", mint_info)
    decoded = coder.types.decode("MintInfo", encoded)

    # Compare decoded values with original
    assert decoded.minted == mint_info["minted"]
    assert decoded.metadata_url == mint_info["metadata_url"]


@pytest.mark.unit
def test_can_encode_and_decode_large_integers():
    """Test that the TypesCoder can encode and decode 128-bit integers."""
    idl_json = {
        "address": "Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS",
        "name": "basic_0",
        "metadata": {
          "name": "basic_0",
          "version": "0.1.0",
          "spec": "0.1.0",
          "description": "Created with Anchor"
        },
        "instructions": [
            {
                "name": "initialize",
                "accounts": [],
                "args": [],
                "discriminator": [],
            },
        ],
        "types": [
            {
                "name": "IntegerTest",
                "type": {
                    "kind": "struct",
                    "fields": [
                        {
                            "name": "unsigned",
                            "type": "u128",
                        },
                        {
                            "name": "signed",
                            "type": "i128",
                        },
                    ],
                },
            },
        ],
    }
    idl = Idl.from_json(json.dumps(idl_json))
    coder = Coder(idl)

    integer_test = {
        "unsigned": 2588012355,
        "signed": -93842345,
    }
    encoded = coder.types.encode("IntegerTest", integer_test)
    decoded = coder.types.decode("IntegerTest", encoded)

    assert decoded.unsigned == integer_test["unsigned"]
    assert decoded.signed == integer_test["signed"]
