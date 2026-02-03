#!/usr/bin/env python3
"""
GUARDIAN Setup Script
Initializes wallet, deploys contracts, configures environment
"""
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

PROJECT_ROOT = Path(__file__).parent.parent
WALLET_PATH = PROJECT_ROOT / "wallet.json"
ENV_PATH = PROJECT_ROOT / ".env"
DATA_DIR = PROJECT_ROOT / "data"


def print_step(msg):
    print(f"{CYAN}➜{RESET} {msg}")


def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")


def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")


def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")


def run_cmd(cmd, check=True, capture=False):
    """Run a shell command"""
    print(f"  {BOLD}${RESET} {cmd}")
    result = subprocess.run(
        cmd, 
        shell=True, 
        capture_output=capture,
        text=True
    )
    if check and result.returncode != 0:
        print_error(f"Command failed with code {result.returncode}")
        if capture:
            print(result.stderr)
        return None
    return result


def check_dependencies():
    """Check required tools are installed"""
    print_step("Checking dependencies...")
    
    deps = {
        "solana": "solana --version",
        "anchor": "anchor --version",
        "python": "python --version",
        "node": "node --version",
    }
    
    missing = []
    for name, cmd in deps.items():
        result = run_cmd(cmd, check=False, capture=True)
        if result and result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            print_success(f"{name}: {version}")
        else:
            print_error(f"{name}: NOT FOUND")
            missing.append(name)
    
    if "solana" in missing:
        print_warning("Solana CLI not found. Install from: https://docs.solana.com/cli/install-solana-cli-tools")
    
    return len(missing) == 0


def setup_wallet():
    """Create or load wallet"""
    print_step("Setting up wallet...")
    
    if WALLET_PATH.exists():
        print_success(f"Wallet exists: {WALLET_PATH}")
        # Show address
        result = run_cmd(f"solana address -k {WALLET_PATH}", capture=True)
        if result and result.returncode == 0:
            print(f"  Address: {result.stdout.strip()}")
        return True
    
    print_warning("No wallet found, creating new one...")
    result = run_cmd(f"solana-keygen new --outfile {WALLET_PATH} --no-bip39-passphrase", capture=True)
    
    if result and result.returncode == 0:
        print_success("Wallet created!")
        # Show address
        result = run_cmd(f"solana address -k {WALLET_PATH}", capture=True)
        if result:
            print(f"  Address: {result.stdout.strip()}")
        return True
    
    print_error("Failed to create wallet")
    return False


def setup_solana_config():
    """Configure Solana CLI for devnet"""
    print_step("Configuring Solana for devnet...")
    
    run_cmd("solana config set --url devnet")
    run_cmd(f"solana config set --keypair {WALLET_PATH}")
    
    print_success("Solana configured for devnet")


def request_airdrop():
    """Request devnet SOL"""
    print_step("Requesting devnet airdrop...")
    
    # Check current balance
    result = run_cmd(f"solana balance -k {WALLET_PATH}", capture=True)
    if result:
        balance = result.stdout.strip()
        print(f"  Current balance: {balance}")
        
        # Parse balance
        try:
            sol = float(balance.split()[0])
            if sol >= 2:
                print_success("Sufficient balance for deployment")
                return True
        except:
            pass
    
    # Request airdrop
    print_warning("Requesting 2 SOL airdrop...")
    result = run_cmd(f"solana airdrop 2 -k {WALLET_PATH}", capture=True)
    
    if result and result.returncode == 0:
        print_success("Airdrop received!")
        return True
    else:
        print_warning("Airdrop may have failed - devnet limits apply")
        return True  # Continue anyway


def setup_env():
    """Create .env file"""
    print_step("Setting up environment...")
    
    if ENV_PATH.exists():
        print_success(".env file exists")
        return True
    
    env_content = """# GUARDIAN Configuration
# Network: devnet or mainnet-beta
NETWORK=devnet

# Solana RPC (Helius recommended for better rate limits)
SOLANA_RPC_URL=https://api.devnet.solana.com
# SOLANA_RPC_URL=https://devnet.helius-rpc.com/?api-key=YOUR_KEY

# Wallet path
WALLET_PATH=./wallet.json

# Anthropic API Key (required for AI analysis)
ANTHROPIC_API_KEY=your_anthropic_key_here

# Claude model
MODEL=claude-sonnet-4-20250514

# Helius API Key (optional, for enhanced monitoring)
HELIUS_API_KEY=your_helius_key_here
HELIUS_WEBHOOK_SECRET=your_webhook_secret_here

# Alert Channels (optional)
DISCORD_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Agent Settings
SCAN_INTERVAL_SECONDS=30
MIN_THREAT_CONFIDENCE=0.6
MAX_MEMORY_ENTRIES=1000
"""
    
    with open(ENV_PATH, 'w') as f:
        f.write(env_content)
    
    print_success(f"Created .env file at {ENV_PATH}")
    print_warning("⚠️  Edit .env and add your API keys!")
    return True


def setup_directories():
    """Create required directories"""
    print_step("Creating directories...")
    
    dirs = [
        DATA_DIR,
        DATA_DIR / "models",
        PROJECT_ROOT / "target" / "idl",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print_success(f"Created: {d}")


def build_contracts():
    """Build Anchor smart contracts"""
    print_step("Building smart contracts...")
    
    os.chdir(PROJECT_ROOT)
    result = run_cmd("anchor build", capture=True)
    
    if result and result.returncode == 0:
        print_success("Smart contracts built!")
        return True
    else:
        print_error("Build failed")
        if result:
            print(result.stderr)
        return False


def deploy_contracts():
    """Deploy contracts to devnet"""
    print_step("Deploying to devnet...")
    
    os.chdir(PROJECT_ROOT)
    result = run_cmd("anchor deploy --provider.cluster devnet", capture=True)
    
    if result and result.returncode == 0:
        print_success("Contracts deployed!")
        
        # Extract program IDs from output
        lines = result.stdout.split('\n')
        for line in lines:
            if "Program Id:" in line:
                print(f"  {line.strip()}")
        
        return True
    else:
        print_error("Deployment failed")
        if result:
            print(result.stderr)
        return False


def install_python_deps():
    """Install Python dependencies"""
    print_step("Installing Python dependencies...")
    
    req_file = PROJECT_ROOT / "agents" / "requirements.txt"
    result = run_cmd(f"pip install -r {req_file}", capture=True)
    
    if result and result.returncode == 0:
        print_success("Python dependencies installed!")
        return True
    else:
        print_warning("Some dependencies may have failed to install")
        return True


def main():
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════╗
║                     GUARDIAN SETUP                                ║
║                Solana Immune System                              ║
╚══════════════════════════════════════════════════════════════════╝{RESET}
    """)
    
    # Check what's available
    has_deps = check_dependencies()
    
    print()
    setup_directories()
    
    print()
    setup_env()
    
    print()
    install_python_deps()
    
    if has_deps:
        print()
        setup_wallet()
        
        print()
        setup_solana_config()
        
        print()
        request_airdrop()
        
        print()
        if build_contracts():
            print()
            deploy_contracts()
    
    print(f"""
{BOLD}{GREEN}
╔══════════════════════════════════════════════════════════════════╗
║                     SETUP COMPLETE!                              ║
╚══════════════════════════════════════════════════════════════════╝{RESET}

Next steps:
  1. Edit {ENV_PATH} with your API keys
  2. Run the CLI:     python cli.py
  3. Start the swarm: python agents/swarm.py
  4. View dashboard:  open app/dashboard/index.html

For help: python cli.py help
    """)


if __name__ == "__main__":
    main()
