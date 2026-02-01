test:
	uv run --all-extras pytest -vv

init-clientgen-examples:
	cd tests/client_gen/example-program/ && anchor idl parse -f programs/example-program/src/lib.rs -o ../../idls/clientgen_example_program.json && cd ../../.. && uv run anchorpy client-gen tests/idls/clientgen_example_program.json tests/client_gen/example_program_gen --pdas
	uv run anchorpy client-gen tests/idls/basic_2.json examples/client-gen/basic_2
	uv run anchorpy client-gen tests/idls/tictactoe.json examples/client-gen/tictactoe

lint:
	uv run ruff src tests
	uv run mypy src tests
