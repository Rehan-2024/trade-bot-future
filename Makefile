.PHONY: install test lint format typecheck run-interactive

install:
	python -m pip install -r requirements.txt -r requirements-dev.txt

test:
	pytest tests/ -v --cov=bot --cov-report=term-missing

lint:
	ruff check bot tests cli.py

format:
	ruff format bot tests cli.py

format-check:
	ruff format bot tests cli.py --check

typecheck:
	mypy bot

run-interactive:
	python cli.py interactive
