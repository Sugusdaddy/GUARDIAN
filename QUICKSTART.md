# GUARDIAN Quick Reference

## 🌐 **ACCESS WEB DASHBOARD (START HERE!)**

### Fastest Way to See GUARDIAN

```bash
# 1. Install
git clone https://github.com/Sugusdaddy/GUARDIAN.git
cd GUARDIAN
pip install -e .

# 2. Start Web Server
python app/api/main.py

# 3. Open Browser
# 🌐 http://localhost:8000
```

**Your dashboard is now live at: http://localhost:8000** ✨

📖 **Complete guide**: [WEB_ACCESS.md](WEB_ACCESS.md)

---

## Installation

```bash
git clone https://github.com/Sugusdaddy/GUARDIAN.git
cd GUARDIAN
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your API keys
```

## Essential Commands

### CLI
```bash
python cli.py              # Interactive mode
python cli.py status       # Quick status
python cli.py help         # Show commands
```

### API Server
```bash
python app/api/main.py     # Start API
# Open http://localhost:8000/docs
```

### Development
```bash
make install-dev           # Install deps
make test                  # Run tests
make format                # Format code
make lint                  # Check code
make all                   # All checks
```

## Key Files

- **`.env`** - Configuration and API keys
- **`cli.py`** - Command-line interface
- **`agents/`** - Core agent framework
- **`GUARDIAN/`** - Elite agents
- **`app/api/`** - REST API
- **`docs/`** - Documentation

## Common Tasks

### Check Status
```python
# CLI
> status

# API
curl http://localhost:8000/api/status
```

### Evaluate Swap
```python
import requests
response = requests.post(
    "http://localhost:8000/api/swap/evaluate",
    json={
        "user_wallet": "...",
        "input_mint": "SOL",
        "output_mint": "TOKEN",
        "amount": 1.0
    }
)
print(response.json()["action"])  # APPROVE/WARN/REJECT
```

### Emergency Evacuation
```python
response = requests.post(
    "http://localhost:8000/api/evacuate/emergency",
    json={
        "source_wallet": "compromised_wallet",
        "destination_wallet": "safe_wallet",
        "urgency": "CRITICAL"
    }
)
```

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Network
NETWORK=devnet                    # or mainnet-beta
SOLANA_RPC_URL=https://api.devnet.solana.com

# Optional
HELIUS_API_KEY=...
TELEGRAM_BOT_TOKEN=...
DISCORD_WEBHOOK_URL=...
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/threats` | GET | List threats |
| `/api/agents` | GET | Agent statistics |
| `/api/swap/evaluate` | POST | Evaluate swap risk |
| `/api/evacuate/emergency` | POST | Emergency evacuation |

## Agent Roles

| Agent | Role |
|-------|------|
| SENTINEL | Monitor transactions |
| SCANNER | Analyze contracts |
| ORACLE | Predict risks |
| COORDINATOR | Orchestrate swarm |
| GUARDIAN | Active defense |
| INTEL | Knowledge base |
| REPORTER | Alerts |
| AUDITOR | Verification |
| HUNTER | Track attackers |
| HEALER | Recovery |
| HONEYPOT | Trap attackers |
| LAZARUS | Counter-intel |
| NETWORK | Infrastructure |
| QUANTUM | Future-proof |
| SWAPGUARD | Trading protection |
| EVACUATOR | Emergency response |

## Troubleshooting

### CLI won't start
```bash
source venv/bin/activate
pip install -e ".[dev]"
```

### API connection error
```bash
# Check if server is running
curl http://localhost:8000/api/status
```

### Import errors
```bash
# Ensure virtual environment is activated
which python  # Should point to venv/bin/python
pip list      # Check installed packages
```

### Database issues
```bash
rm data/guardian.db
python scripts/setup.py
```

## Resources

- [Full Documentation](docs/README.md)
- [Installation Guide](docs/INSTALLATION.md)
- [Usage Guide](docs/USAGE.md)
- [API Reference](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)

## Need Help?

- **Issues**: https://github.com/Sugusdaddy/GUARDIAN/issues
- **Discussions**: https://github.com/Sugusdaddy/GUARDIAN/discussions
- **Security**: See SECURITY.md
