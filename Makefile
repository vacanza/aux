.PHONY: help install install-dev lint format check test test-cov clean pre-commit run

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install all dependencies including dev tools"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with ruff"
	@echo "  check        Run all checks (lint + format check)"
	@echo "  quality      Run lint, format, and tests"
	@echo "  test         Run pytest tests"
	@echo "  test-cov     Run tests with coverage report"
	@echo "  pre-commit   Run all pre-commit hooks"
	@echo "  run          Run the main script"
	@echo "  clean        Clean up temporary files"

# Installation targets
install:
	pip install requests pyyaml

install-dev:
	pip install -r requirements.txt
	pre-commit install

# Code quality targets
lint:
	ruff check .

format:
	ruff format .

check:
	ruff check .
	ruff format --check .

# Full quality check including tests
quality: lint format test

# Testing targets
test:
	@echo "Running pytest tests..."
	python -m pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	python -m pytest tests/ --cov=scripts --cov-report=term-missing --cov-report=html

# Pre-commit targets
pre-commit:
	pre-commit run --all-files

# Run targets
run:
	python scripts/fetch_downloads.py

# Cleanup targets
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
