test:
	poetry run pytest -vv

init-clientgen-examples:
	poetry run anchorpy client-gen ts-reference/tests/example-program-gen/idl.json tests/client-gen/example_program_gen --program-id 3rTQ3R4B2PxZrAyx7EUefySPgZY8RhJf16cZajbmrzp8
	poetry run anchorpy client-gen tests/idls/basic_2.json examples/client-gen/basic_2 --program-id 3rTQ3R4B2PxZrAyx7EUefySPgZY8RhJf16cZajbmrzp8
	poetry run anchorpy client-gen tests/idls/tictactoe.json examples/client-gen/tictactoe --program-id 3rTQ3R4B2PxZrAyx7EUefySPgZY8RhJf16cZajbmrzp8

lint:
	poetry run flake8
	poetry run mypy src tests
