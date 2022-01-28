test:
	poetry run pytest -vv

lint:
	poetry run flake8
	poetry run mypy src tests
