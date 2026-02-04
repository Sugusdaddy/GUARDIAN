.PHONY: help install install-dev test lint format type-check clean run-cli run-api run-swarm docs

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -e .

install-dev:  ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage report
	pytest --cov=agents --cov=GUARDIAN --cov=app --cov-report=html --cov-report=term

lint:  ## Run linting checks (flake8)
	flake8 agents/ GUARDIAN/ app/ cli.py --max-line-length=100 --extend-ignore=E203,W503

format:  ## Format code with black and isort
	black agents/ GUARDIAN/ app/ cli.py scripts/
	isort agents/ GUARDIAN/ app/ cli.py scripts/

format-check:  ## Check code formatting without making changes
	black --check agents/ GUARDIAN/ app/ cli.py scripts/
	isort --check agents/ GUARDIAN/ app/ cli.py scripts/

type-check:  ## Run type checking with mypy
	mypy agents/ GUARDIAN/ app/ cli.py --ignore-missing-imports

pre-commit:  ## Run all pre-commit hooks
	pre-commit run --all-files

clean:  ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ .coverage htmlcov/

run-cli:  ## Run the interactive CLI
	python cli.py

run-api:  ## Run the API server
	python app/api/main.py

run-swarm:  ## Start the agent swarm
	python agents/swarm.py

demo:  ## Run simulation demo
	python scripts/demo_simulation.py -n 50

setup:  ## Run initial setup
	python scripts/setup.py

docs:  ## Build documentation
	cd docs && make html

all: format lint type-check test  ## Run all checks (format, lint, type-check, test)
