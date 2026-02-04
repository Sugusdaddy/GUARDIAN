# System Architecture

## Overview

GUARDIAN is a distributed multi-agent system designed to provide 24/7 autonomous security for the Solana blockchain ecosystem. The system consists of 16 specialized AI agents working in concert to detect, analyze, and respond to security threats in real-time.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        GUARDIAN System                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐      │
│  │   Web UI     │   │  Telegram    │   │  REST API    │      │
│  │  Dashboard   │   │     Bot      │   │   Clients    │      │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘      │
│         │                   │                   │              │
│         └───────────────────┴───────────────────┘              │
│                             │                                  │
│                   ┌─────────▼─────────┐                        │
│                   │    FastAPI Server  │                        │
│                   │   (HTTP/WebSocket) │                        │
│                   └─────────┬─────────┘                        │
│                             │                                  │
│         ┌───────────────────┼───────────────────┐              │
│         │                   │                   │              │
│  ┌──────▼───────┐   ┌──────▼──────┐   ┌───────▼──────┐       │
│  │  COORDINATOR  │   │   Database   │   │   On-Chain   │       │
│  │    Agent      │◄──┤   (SQLite)   │   │  Contracts   │       │
│  └──────┬───────┘   └──────────────┘   └──────────────┘       │
│         │                                                       │
│         │  Agent Swarm Orchestration                           │
│         │                                                       │
│  ┌──────┴──────────────────────────────────────────────┐      │
│  │                                                       │      │
│  │  Core Defense Squad (10 Agents)                      │      │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │      │
│  │  │SENTINEL │ │ SCANNER │ │ ORACLE  │ │GUARDIAN │   │      │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │      │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │      │
│  │  │  INTEL  │ │REPORTER │ │ AUDITOR │ │ HUNTER  │   │      │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │      │
│  │  ┌─────────┐ ┌─────────┐                            │      │
│  │  │ HEALER  │ │  (more) │                            │      │
│  │  └─────────┘ └─────────┘                            │      │
│  │                                                       │      │
│  │  Elite Threat Squad (6 Advanced Agents)              │      │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐  │      │
│  │  │HONEYPOT │ │LAZARUS  │ │ NETWORK  │ │ QUANTUM │  │      │
│  │  └─────────┘ └─────────┘ └──────────┘ └─────────┘  │      │
│  │  ┌──────────┐ ┌──────────┐                          │      │
│  │  │SWAPGUARD │ │EVACUATOR │                          │      │
│  │  └──────────┘ └──────────┘                          │      │
│  └───────────────────────────────────────────────────┘       │
│                             │                                  │
│                   ┌─────────▼─────────┐                        │
│                   │  External Services │                        │
│                   ├────────────────────┤                        │
│                   │ • Solana RPC       │                        │
│                   │ • Anthropic API    │                        │
│                   │ • Helius API       │                        │
│                   │ • Jupiter API      │                        │
│                   └────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Agent Framework

#### Base Agent Class
All agents inherit from `AutonomousAgent`, which provides:
- Autonomous decision-making loop
- Claude Opus integration for reasoning
- Database persistence
- On-chain commitment capabilities
- ML-based risk scoring

#### Agent Communication
- **Coordinator-based**: COORDINATOR agent orchestrates multi-agent decisions
- **Event-driven**: Agents can emit and subscribe to events
- **Database-shared**: Shared threat intelligence via SQLite
- **Consensus**: Multi-agent voting for critical decisions

### 2. Data Layer

#### Database (SQLite)
- **Threats table**: All detected threats with evidence
- **Agents table**: Agent statistics and activity logs
- **Blacklist**: Known malicious addresses
- **Watchlist**: Monitored addresses
- **Patterns**: Learned threat patterns
- **Actions**: Agent action history

#### On-Chain Storage (Solana)
- **Reasoning Registry**: Commit/reveal for transparent AI decisions
- **Threat Intelligence**: Decentralized threat database
- **Agent Coordinator**: Multi-sig actions and swarm coordination

### 3. API Layer

#### FastAPI Server
- **REST endpoints**: CRUD operations for threats, agents, intelligence
- **WebSocket**: Real-time updates and notifications
- **OpenAPI**: Auto-generated documentation
- **CORS**: Enabled for web dashboard

#### Key Endpoints
- `/api/status` - System health
- `/api/threats` - Threat management
- `/api/agents` - Agent statistics
- `/api/swap/*` - SwapGuard risk evaluation
- `/api/evacuate/*` - Emergency wallet protection

### 4. Frontend

#### Web Dashboard
- Real-time threat monitoring
- Agent activity visualization
- Risk assessment tools
- Emergency controls

#### CLI Interface
- Interactive command-line interface
- Full system control
- Testing and simulation tools

## Agent Roles

### Core Defense Squad (10 Agents)

| Agent | Role | Primary Function |
|-------|------|------------------|
| **SENTINEL** | Monitor | Real-time transaction monitoring, whale alerts |
| **SCANNER** | Analyze | Contract vulnerability scanning, rug pull detection |
| **ORACLE** | Predict | ML-powered risk prediction, campaign detection |
| **COORDINATOR** | Orchestrate | Multi-agent coordination, consensus building |
| **GUARDIAN** | Defend | Active threat defense, emergency response |
| **INTEL** | Knowledge | Threat intelligence database, pattern library |
| **REPORTER** | Alert | Community notifications, user warnings |
| **AUDITOR** | Verify | On-chain reasoning verification, auditing |
| **HUNTER** | Track | Malicious actor tracking, fund flow analysis |
| **HEALER** | Recover | Fund recovery, victim assistance |

### Elite Threat Squad (6 Advanced Agents)

| Agent | Role | Primary Function |
|-------|------|------------------|
| **HONEYPOT** | Trap | Deploys bait wallets, captures attacker methods |
| **LAZARUS** | Counter-Intel | Tracks DPRK/Lazarus Group operations |
| **NETWORK** | Infrastructure | Monitors network health, DDoS detection |
| **QUANTUM** | Future-Proof | Post-quantum cryptography assessment |
| **SWAPGUARD** | Trading | Risk-aware DEX trading protection |
| **EVACUATOR** | Emergency | Emergency wallet evacuation |

## Data Flow

### Threat Detection Flow

```
1. SENTINEL monitors transactions
   ↓
2. Detects suspicious pattern
   ↓
3. Creates threat record in database
   ↓
4. COORDINATOR notifies relevant agents
   ↓
5. Agents analyze (SCANNER, ORACLE, etc.)
   ↓
6. Multi-agent consensus via COORDINATOR
   ↓
7. Decision committed on-chain (AUDITOR)
   ↓
8. Action executed (GUARDIAN, REPORTER)
   ↓
9. Results logged and learned (INTEL)
```

### SwapGuard Flow

```
1. User initiates swap via API
   ↓
2. SWAPGUARD agent evaluates:
   - Token contract analysis
   - Liquidity check
   - Blacklist check
   - Historical patterns
   ↓
3. ML model scores risk
   ↓
4. Decision: APPROVE/WARN/LIMIT/REJECT
   ↓
5. Safe parameters returned to user
```

### Evacuator Flow

```
1. Threat detected or user triggers emergency
   ↓
2. EVACUATOR analyzes wallet:
   - SOL balance
   - SPL tokens
   - NFTs
   - Active approvals
   ↓
3. Creates evacuation plan
   ↓
4. Executes parallel transactions:
   - Transfer all assets
   - Revoke approvals
   ↓
5. Verifies completion
```

## Machine Learning Pipeline

### Components

1. **Embeddings** - sentence-transformers for semantic similarity
2. **Clustering** - DBSCAN for coordinated attack detection
3. **Classification** - Random Forest for risk scoring
4. **Anomaly Detection** - Isolation Forest for unusual patterns
5. **Pattern Learning** - Automatic extraction from history

### Training

- **Online learning**: Models update with new threat data
- **Feedback loop**: Agent decisions improve models
- **Transfer learning**: Pre-trained models fine-tuned for Solana

## Security Considerations

### API Security
- Rate limiting (planned)
- Authentication (planned)
- Input validation
- SQL injection prevention (parameterized queries)

### Agent Security
- API key encryption
- Wallet key security
- On-chain verification
- Transparent reasoning

### Database Security
- SQLite with proper permissions
- No sensitive keys in database
- Regular backups recommended

## Scalability

### Current Limitations
- Single SQLite database
- Single server instance
- No horizontal scaling

### Future Improvements
- PostgreSQL for production
- Redis for caching
- Kubernetes deployment
- Multi-region support

## Performance

### Metrics
- **Detection time**: ~15 seconds average
- **API latency**: <100ms for most endpoints
- **Agent cycle**: 30 seconds (configurable)
- **Concurrent agents**: 16

### Optimization
- Async/await throughout
- Connection pooling
- Lazy loading
- Caching where appropriate

## Deployment

### Development
```bash
python cli.py          # CLI interface
python app/api/main.py # API server
python agents/swarm.py # Agent swarm
```

### Production (Planned)
- Docker containers
- Kubernetes orchestration
- Load balancing
- Auto-scaling

## Monitoring

### Logs
- Structured logging with structlog
- Log levels: DEBUG, INFO, WARNING, ERROR
- Agent activity tracking
- Performance metrics

### Metrics
- Threats detected
- Agent actions
- API requests
- System health

## Technology Stack

### Backend
- **Python 3.10+**: Core language
- **FastAPI**: Web framework
- **SQLite**: Database
- **Anthropic Claude**: AI reasoning
- **scikit-learn**: Machine learning
- **sentence-transformers**: Embeddings

### Blockchain
- **Solana**: Layer 1 blockchain
- **Anchor**: Smart contract framework
- **solana-py**: Python client
- **SPL Token**: Token standard

### Frontend
- **HTML/CSS/JavaScript**: Web dashboard
- **WebSocket**: Real-time updates
- **Rich**: CLI interface

## Future Enhancements

### Planned Features
1. Authentication and authorization
2. Multi-user support
3. Custom agent creation
4. Plugin system
5. Mobile app
6. Browser extension
7. DAO governance
8. Token launch

### Research Areas
1. Advanced ML models
2. Zero-knowledge proofs
3. Cross-chain analysis
4. Quantum-resistant cryptography
5. Decentralized coordination

## References

- [Solana Documentation](https://docs.solana.com/)
- [Anthropic Claude](https://www.anthropic.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Anchor Framework](https://www.anchor-lang.com/)
