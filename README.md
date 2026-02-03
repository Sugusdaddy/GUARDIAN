# 🛡️ GUARDIAN - Solana Immune System

> Autonomous Multi-Agent Security Infrastructure for Solana

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Solana](https://img.shields.io/badge/Solana-Devnet-purple)](https://solana.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)

**Protecting the Solana ecosystem 24/7 with AI-powered threat detection and response.**

## 🎯 The Problem

- **$3.4B** stolen from DeFi in 2024
- **93%** of new DEX pools are scams
- Current security is **reactive**, not proactive
- Users lose funds **before** anyone can warn them

## 💡 The Solution

GUARDIAN is a multi-agent autonomous swarm that protects the Solana ecosystem in **real-time**:

- 🔭 **Continuous monitoring** of transactions and contracts
- 🧠 **AI-powered analysis** using Claude Opus
- 🤖 **ML-based prediction** with embeddings and clustering
- 🤝 **Swarm coordination** for complex threats
- 🔐 **Verifiable reasoning** published on-chain
- ⚡ **Autonomous response** without human intervention

## ✨ Features

### 🤖 10 Specialized Agents

| Agent | Role | Description |
|-------|------|-------------|
| 🔭 SENTINEL | Monitor | Transaction monitoring, whale alerts |
| 🔍 SCANNER | Analyze | Contract and token vulnerability scanning |
| 🔮 ORACLE | Predict | ML-powered risk prediction and campaign detection |
| 🎯 COORDINATOR | Orchestrate | Swarm coordination and consensus |
| 🛡️ GUARDIAN | Defend | Active threat defense |
| 📚 INTEL | Knowledge | Threat intelligence database |
| 📢 REPORTER | Alert | Community notifications |
| ✅ AUDITOR | Verify | Reasoning verification |
| 🔍 HUNTER | Track | Malicious actor tracking |
| 💚 HEALER | Recover | Fund recovery attempts |

### 🧠 Machine Learning

- **Embeddings** - Semantic threat similarity using sentence-transformers
- **Clustering** - DBSCAN to detect coordinated attack campaigns
- **Classification** - Random Forest for risk scoring
- **Anomaly Detection** - Isolation Forest for unusual patterns
- **Pattern Learning** - Automatic pattern extraction from history

### 🔐 Verifiable Reasoning

Every agent decision is cryptographically committed on-chain **BEFORE** execution:

```
1. COMMIT  → Hash reasoning, publish to chain
2. EXECUTE → Perform the security action  
3. REVEAL  → Publish full reasoning text
4. VERIFY  → Anyone can verify hash matches
```

### 📊 Dashboard & API

- **Real-time dashboard** with WebSocket updates
- **REST API** for integrations
- **CLI** for interactive operations
- **Telegram bot** for mobile alerts

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Anchor 0.30+ (optional, for smart contracts)
- Solana CLI (optional)

### Installation

```bash
# Clone the repo
git clone https://github.com/Sugusdaddy/GUARDIAN.git
cd GUARDIAN

# Run setup
python scripts/setup.py

# Edit configuration
nano .env  # Add your API keys
```

### Configuration

Create `.env` file:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Network
NETWORK=devnet
SOLANA_RPC_URL=https://api.devnet.solana.com

# Optional - Enhanced monitoring
HELIUS_API_KEY=your_helius_key

# Optional - Alerts
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
DISCORD_WEBHOOK_URL=your_webhook_url
```

### Run

```bash
# Interactive CLI
python cli.py

# Run simulation demo
python scripts/demo_simulation.py -n 50

# Start the swarm
python agents/swarm.py

# Start API server + dashboard
python app/api/main.py
# Open http://localhost:8000

# Start Telegram bot
python agents/bots/telegram_bot.py
```

## 📁 Project Structure

```
GUARDIAN/
├── agents/                 # Python agent framework
│   ├── core/              # Core components
│   │   ├── base_agent.py  # Base autonomous agent
│   │   ├── database.py    # SQLite persistence
│   │   ├── embeddings.py  # ML & embeddings
│   │   ├── onchain.py     # Solana integration
│   │   └── config.py      # Configuration
│   ├── specialized/       # 10 specialized agents
│   ├── integrations/      # Helius, Jupiter, etc.
│   ├── webhooks/          # Real-time event server
│   ├── bots/              # Telegram bot
│   └── tests/             # Test suite
├── programs/              # Anchor smart contracts
│   ├── reasoning-registry/
│   ├── threat-intelligence/
│   └── agent-coordinator/
├── app/
│   ├── api/               # FastAPI backend
│   └── dashboard/         # Web dashboard
├── scripts/               # Setup and demo scripts
├── data/                  # Database and models
├── cli.py                 # Interactive CLI
└── .env                   # Configuration
```

## 🔧 CLI Commands

```bash
python cli.py

# Commands:
help                    # Show help
status                  # System status
threats [active|all]    # List threats
threat <id>             # Threat details
blacklist [list|add|remove]  # Manage blacklist
watchlist [list|add]    # Manage watchlist
agents                  # Agent statistics
patterns                # Learned patterns
score <address>         # Risk assessment
simulate <type>         # Simulate threat
swarm start             # Start agent swarm
wallet                  # Wallet info
airdrop [amount]        # Request devnet SOL
export <file>           # Export data
```

## 📡 API Endpoints

```
GET  /api/status              # System status
GET  /api/threats             # List threats
GET  /api/threats/{id}        # Threat details
POST /api/threats             # Create threat
GET  /api/blacklist           # Get blacklist
POST /api/blacklist           # Add to blacklist
GET  /api/agents              # Agent stats
POST /api/score               # Risk scoring
WS   /ws                      # Real-time updates
```

## 🤖 Telegram Bot Commands

```
/start      # Welcome message
/status     # System status  
/threats    # Recent threats
/blacklist  # View blacklist
/score <addr>  # Risk assessment
/alert on|off  # Toggle alerts
```

## 🔬 Smart Contracts

### Reasoning Registry
On-chain commit/reveal for transparent AI reasoning.

### Threat Intelligence
Decentralized threat database with multi-agent consensus.

### Agent Coordinator
Swarm coordination and multi-sig actions.

Deploy to devnet:
```bash
anchor build
anchor deploy --provider.cluster devnet
```

## 📈 Metrics

| Metric | Target |
|--------|--------|
| Detection Time | < 30s |
| False Positive Rate | < 5% |
| Uptime | 99.9% |

## 🧪 Testing

```bash
# Run all tests
cd agents
pytest

# Run specific tests
pytest tests/test_core.py -v

# Run with coverage
pytest --cov=core tests/
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 🔒 Security

See [SECURITY.md](SECURITY.md) for security policy.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Documentation:** [docs/](docs/)
- **Demo Video:** [YouTube](#)
- **Discord:** [Join Community](#)
- **Twitter:** [@SolanaImmune](#)

---

## 🏆 Hackathon

Built for the **Solana AI Hackathon** by Colosseum.

**Protecting Solana, one block at a time.** 🛡️
