# Usage Guide

## Quick Start

### 1. Start the CLI

```bash
python cli.py
```

### 2. Check System Status

```
> status
```

### 3. List Active Threats

```
> threats active
```

### 4. Start the Agent Swarm

```
> swarm start
```

## Interactive CLI

The GUARDIAN CLI provides an interactive interface for monitoring and managing the system.

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `help` | Show available commands | `help` |
| `status` | System status and statistics | `status` |
| `threats [filter]` | List threats | `threats active` |
| `threat <id>` | Show threat details | `threat 123` |
| `blacklist [action]` | Manage blacklist | `blacklist list` |
| `watchlist [action]` | Manage watchlist | `watchlist add` |
| `agents` | Show agent statistics | `agents` |
| `patterns` | Show learned patterns | `patterns` |
| `score <address>` | Score address risk | `score So11...` |
| `simulate <type>` | Simulate threat | `simulate rug_pull` |
| `swarm [action]` | Control agent swarm | `swarm start` |
| `wallet` | Show wallet info | `wallet` |
| `airdrop [amount]` | Request devnet SOL | `airdrop 2` |
| `export <file>` | Export data to JSON | `export data.json` |
| `quit` | Exit CLI | `quit` |

### Examples

#### Check System Status

```bash
> status

╭─────────────────── 🛡️ GUARDIAN Status ───────────────────╮
│                                                           │
│ Threats:                                                  │
│   Active: 5                                               │
│   Resolved: 120                                           │
│   Last 24h: 8                                             │
│   Avg Severity: 45.2                                      │
│                                                           │
│ Intelligence:                                             │
│   Blacklisted: 15                                         │
│   Watched: 8                                              │
│   Agents Active: 16                                       │
│                                                           │
│ Configuration:                                            │
│   Network: mainnet-beta                                   │
│   RPC: https://api.mainnet-beta.solana.com               │
│   Model: claude-sonnet-4-20250514                        │
╰───────────────────────────────────────────────────────────╯
```

#### List Active Threats

```bash
> threats active

┏━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ ID  ┃ Type       ┃ Severity ┃ Target      ┃ Status  ┃ Detected    ┃
┡━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 123 │ rug_pull   │ 85       │ Token...    │ active  │ 2h ago      │
│ 124 │ phishing   │ 70       │ Wallet...   │ active  │ 1h ago      │
└─────┴────────────┴──────────┴─────────────┴─────────┴─────────────┘
```

#### Score an Address

```bash
> score So11111111111111111111111111111111111111112

Risk Score: 15.5 (LOW)
Factors:
  - Blacklisted: No
  - Age: 2 years
  - Activity: High
  - Patterns: Normal
```

## API Server

### Starting the Server

```bash
# Start API server
python app/api/main.py

# Or use make
make run-api
```

The server will start on `http://localhost:8000`.

### Accessing the Dashboard

Open your browser to:
- **Dashboard:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### API Examples

#### Get System Status (curl)

```bash
curl http://localhost:8000/api/status
```

#### Get System Status (Python)

```python
import requests

response = requests.get("http://localhost:8000/api/status")
print(response.json())
```

#### Evaluate a Swap

```python
import requests

swap_data = {
    "user_wallet": "YourWallet...",
    "input_mint": "So11111111111111111111111111111111111111112",
    "output_mint": "TokenMint...",
    "amount": 1.0
}

response = requests.post(
    "http://localhost:8000/api/swap/evaluate",
    json=swap_data
)

decision = response.json()
if decision["action"] == "APPROVE":
    print(f"✅ Safe to swap with {decision['risk_level']} risk")
else:
    print(f"⛔ Swap blocked: {decision['warnings']}")
```

#### Emergency Evacuation

```python
import requests

evacuation_data = {
    "source_wallet": "CompromisedWallet...",
    "destination_wallet": "SafeWallet...",
    "urgency": "CRITICAL"
}

response = requests.post(
    "http://localhost:8000/api/evacuate/emergency",
    json=evacuation_data
)

result = response.json()
print(f"Evacuated ${result['total_evacuated_usd']:.2f}")
```

## Agent Swarm

### Starting the Swarm

```bash
python agents/swarm.py

# Or via CLI
python cli.py
> swarm start
```

The swarm will activate all 16 agents:
- 10 Core Defense Squad agents
- 6 Elite Threat Squad agents

### Monitoring Agents

```bash
# In CLI
> agents

┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Agent       ┃ Role        ┃ Actions  ┃ Status          ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ SENTINEL    │ Monitor     │ 1,234    │ ✓ Active        │
│ SCANNER     │ Analyze     │ 856      │ ✓ Active        │
│ ORACLE      │ Predict     │ 432      │ ✓ Active        │
│ ...         │ ...         │ ...      │ ...             │
└─────────────┴─────────────┴──────────┴─────────────────┘
```

## Telegram Bot

### Starting the Bot

```bash
# Configure bot token in .env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Start bot
python agents/bots/telegram_bot.py
```

### Bot Commands

- `/start` - Welcome message
- `/status` - System status
- `/threats` - Recent threats
- `/blacklist` - View blacklist
- `/score <address>` - Risk assessment
- `/network` - Network health
- `/alert on|off` - Toggle alerts

## Testing and Simulation

### Run Demo Simulation

```bash
# Simulate 50 threats
python scripts/demo_simulation.py -n 50

# Or use make
make demo
```

### Simulate Specific Threats

```bash
# In CLI
> simulate rug_pull
> simulate phishing
> simulate honeypot
```

## Integration Examples

### Python SDK Usage

```python
from GUARDIAN import evaluate_swap, emergency_evacuate, get_evacuator

# Evaluate a swap
decision = await evaluate_swap(
    user_wallet="...",
    input_mint="SOL",
    output_mint="TOKEN",
    amount=1.0
)

# Emergency evacuation
result = await emergency_evacuate(
    source_wallet="compromised",
    destination_wallet="safe"
)

# Register safe wallet
evacuator = get_evacuator()
evacuator.register_safe_wallet(
    user_wallet="main",
    safe_wallet="cold"
)
```

### JavaScript/TypeScript Integration

```typescript
import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

// Evaluate swap
const evaluateSwap = async (
  userWallet: string,
  inputMint: string,
  outputMint: string,
  amount: number
) => {
  const response = await axios.post(`${BASE_URL}/api/swap/evaluate`, {
    user_wallet: userWallet,
    input_mint: inputMint,
    output_mint: outputMint,
    amount: amount
  });
  return response.data;
};

// Use it
const decision = await evaluateSwap(
  'YourWallet...',
  'So11111111111111111111111111111111111111112',
  'TokenMint...',
  1.0
);

if (decision.action === 'APPROVE') {
  console.log('✅ Safe to swap');
} else {
  console.log('⛔ Swap blocked:', decision.warnings);
}
```

## Best Practices

1. **Always test on devnet first** before using mainnet
2. **Pre-register safe wallets** before emergencies
3. **Monitor agent logs** for anomalies
4. **Keep API keys secure** - never commit them
5. **Use appropriate urgency levels** for evacuations
6. **Review risk scores** before large transactions
7. **Enable Telegram alerts** for real-time notifications
8. **Regular backups** of the database

## Troubleshooting

### CLI Won't Start

```bash
# Check Python version
python --version  # Should be 3.10+

# Reinstall dependencies
pip install -e ".[dev]"
```

### API Connection Errors

```bash
# Check if server is running
curl http://localhost:8000/api/status

# Check logs
python app/api/main.py
```

### Agent Swarm Issues

```bash
# Check database
python -c "from agents.core.database import get_db; print(get_db())"

# Check API key
echo $ANTHROPIC_API_KEY
```

## Advanced Usage

See additional documentation:
- [Architecture](ARCHITECTURE.md) - System design
- [API Reference](API.md) - Complete API documentation
- [Contributing](../CONTRIBUTING.md) - Development guide
