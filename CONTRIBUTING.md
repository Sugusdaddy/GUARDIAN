# Contributing to GUARDIAN

Thank you for your interest in contributing to GUARDIAN!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/GUARDIAN.git`
3. Create a branch: `git checkout -b feature/your-feature-name`

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Coding Standards

- **Line length**: 100 characters
- **Formatting**: Use Black (`make format`)
- **Linting**: Use flake8 (`make lint`)
- **Type hints**: Required for public APIs
- **Docstrings**: Google-style

## Testing

```bash
pytest              # Run all tests
pytest --cov       # With coverage
make test          # Using Makefile
```

## Pull Request Process

1. Update from upstream: `git pull upstream main`
2. Run all checks: `make all`
3. Update documentation if needed
4. Update CHANGELOG.md
5. Submit PR with clear description

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

Thank you for contributing! 🛡️
