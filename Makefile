.PHONY: run test lint install dev

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

run:
	python -m bot

test:
	pytest tests/ -v

lint:
	ruff check bot/ tests/
	ruff format --check bot/ tests/

format:
	ruff format bot/ tests/
