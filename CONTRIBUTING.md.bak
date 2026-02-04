# Contributing to Solana Immune System

Thank you for your interest in contributing to the Solana Immune System!

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Install dependencies (see README.md)
4. Create a new branch for your feature

## Development Setup

### Prerequisites
- Rust 1.70+
- Solana CLI 1.17+
- Anchor 0.30+
- Node.js 18+
- Python 3.10+

### Building

```bash
# Build smart contracts
anchor build

# Install Python dependencies
cd agents
pip install -r requirements.txt
```

### Testing

```bash
# Run Anchor tests
anchor test

# Run Python tests
cd agents
pytest
```

## Code Style

### Rust
- Follow Rust standard formatting (`cargo fmt`)
- Use meaningful variable names
- Document public functions

### Python
- Follow PEP 8
- Use type hints
- Document classes and functions

### TypeScript
- Use Prettier for formatting
- Follow ESLint rules

## Pull Request Process

1. Ensure tests pass
2. Update documentation if needed
3. Write a clear PR description
4. Request review from maintainers

## Agent Development

When adding a new agent:

1. Create a new file in `agents/specialized/`
2. Extend `AutonomousAgent` base class
3. Implement required methods:
   - `scan_environment()`
   - `execute_action()`
4. Add to `__init__.py`
5. Add to swarm in `swarm.py`
6. Write tests

## Smart Contract Development

When modifying contracts:

1. Update the program in `programs/`
2. Run `anchor build` to verify
3. Update tests in `tests/`
4. Document any new instructions

## Questions?

Open an issue or join our Discord.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
