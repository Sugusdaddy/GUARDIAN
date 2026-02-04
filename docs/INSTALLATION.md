# Installation Guide

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher (optional, for smart contracts)
- Anchor 0.30+ (optional, for smart contracts)
- Solana CLI (optional, for blockchain interaction)
- Git

## Quick Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Sugusdaddy/GUARDIAN.git
cd GUARDIAN
```

### 2. Set Up Python Environment

#### Using pip (recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

#### Using Make (Linux/Mac)

```bash
make install-dev
```

### 3. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration with your API keys
nano .env
```

Required environment variables:
```bash
# Anthropic API Key (required)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx

# Network selection
NETWORK=devnet  # or mainnet-beta

# Solana RPC URL
SOLANA_RPC_URL=https://api.devnet.solana.com
```

### 4. Initialize Database

```bash
python scripts/setup.py
```

## Detailed Installation

### Installing from Source

```bash
# Clone repository
git clone https://github.com/Sugusdaddy/GUARDIAN.git
cd GUARDIAN

# Create and activate virtual environment
python3.10 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip

# Install package with all dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Installing Specific Components

#### Core Package Only

```bash
pip install -r requirements.txt
```

#### Development Tools

```bash
pip install -r requirements-dev.txt
```

#### Optional: Machine Learning (for faster processing)

```bash
pip install torch torchvision
```

## Solana Tools Installation (Optional)

### Install Solana CLI

```bash
# Linux/Mac
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Add to PATH
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"

# Verify installation
solana --version
```

### Install Anchor Framework

```bash
# Linux/Mac
cargo install --git https://github.com/coral-xyz/anchor anchor-cli --locked

# Verify installation
anchor --version
```

### Install Node.js Dependencies

```bash
npm install
```

## Database Setup

GUARDIAN uses SQLite by default. The database is automatically created on first run.

### Manual Database Initialization

```bash
python -c "from agents.core.database import get_db; get_db()"
```

## Configuration

### Required Configuration

Edit `.env` file:

```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# Network (choose one)
NETWORK=devnet
# NETWORK=mainnet-beta

# RPC URL
SOLANA_RPC_URL=https://api.devnet.solana.com
```

### Optional Configuration

```bash
# Enhanced monitoring with Helius
HELIUS_API_KEY=your_helius_key

# Alert channels
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
DISCORD_WEBHOOK_URL=your_webhook_url

# Agent settings
SCAN_INTERVAL_SECONDS=30
MIN_THREAT_CONFIDENCE=0.6
MAX_MEMORY_ENTRIES=1000
```

## Verification

### Test Installation

```bash
# Run tests
pytest

# Or using make
make test
```

### Run CLI

```bash
python cli.py
```

You should see the GUARDIAN banner and prompt.

### Start API Server

```bash
python app/api/main.py
```

Visit `http://localhost:8000/docs` to see the API documentation.

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -e ".[dev]"
```

#### 2. Solana Connection Issues

```bash
# Test RPC connection
curl https://api.devnet.solana.com -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'
```

#### 3. Database Errors

```bash
# Remove and recreate database
rm data/guardian.db
python scripts/setup.py
```

#### 4. Missing API Keys

Make sure `ANTHROPIC_API_KEY` is set in `.env`:
```bash
echo $ANTHROPIC_API_KEY  # Should not be empty
```

## Platform-Specific Instructions

### macOS

```bash
# Install Python 3.10+
brew install python@3.10

# Install dependencies
pip3 install -e ".[dev]"
```

### Linux (Ubuntu/Debian)

```bash
# Install Python 3.10+
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# Install system dependencies
sudo apt install build-essential libssl-dev libffi-dev python3-dev
```

### Windows

```powershell
# Install Python from python.org
# Then in PowerShell:

# Create virtual environment
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# Install
pip install -e .[dev]
```

## Docker Installation (Coming Soon)

Docker support is planned for future releases.

## Next Steps

After installation, see:
- [Usage Guide](USAGE.md) - How to use GUARDIAN
- [API Documentation](API.md) - API reference
- [Architecture](ARCHITECTURE.md) - System design
