# API Documentation

## Base URL

- **Development:** `http://localhost:8000`
- **Production:** `https://api.guardian.sol` (coming soon)

## Authentication

Currently, the API is open and does not require authentication. This will be added in future versions.

## Rate Limiting

No rate limiting is currently applied. Please use the API responsibly.

## Response Format

All responses are in JSON format. Successful responses will have a 2xx status code, while errors will have 4xx or 5xx status codes.

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

## Endpoints

### Status

#### GET `/api/status`

Get system status and health information.

**Response:**
```json
{
  "status": "online",
  "timestamp": "2024-01-15T12:00:00",
  "network": "mainnet-beta",
  "model": "claude-sonnet-4-20250514",
  "threats": {
    "active": 5,
    "resolved": 120,
    "last_24h": 8,
    "avg_severity": 45.2
  },
  "agents": {
    "total": 16,
    "active": 16
  },
  "db": {
    "total_threats": 125,
    "total_patterns": 42
  }
}
```

### Threats

#### GET `/api/threats`

List all threats with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by status (`active`, `resolved`, `investigating`)
- `limit` (optional): Maximum number of results (default: 50)

**Response:**
```json
{
  "threats": [
    {
      "id": 1,
      "threat_type": "rug_pull",
      "severity": 85,
      "target_address": "So11111111111111111111111111111111111111112",
      "description": "Suspicious token with hidden mint authority",
      "status": "active",
      "detected_by": "SCANNER",
      "detected_at": "2024-01-15T12:00:00"
    }
  ],
  "total": 1,
  "status": "active"
}
```

#### GET `/api/threats/{id}`

Get detailed information about a specific threat.

**Response:**
```json
{
  "id": 1,
  "threat_type": "rug_pull",
  "severity": 85,
  "target_address": "So11111111111111111111111111111111111111112",
  "description": "Suspicious token with hidden mint authority",
  "evidence": {
    "mint_authority": "present",
    "freeze_authority": "present",
    "liquidity": "low"
  },
  "status": "active",
  "detected_by": "SCANNER",
  "detected_at": "2024-01-15T12:00:00"
}
```

#### POST `/api/threats`

Create a new threat record.

**Request Body:**
```json
{
  "threat_type": "phishing",
  "severity": 70,
  "target_address": "optional_address",
  "description": "Phishing attempt detected",
  "evidence": {
    "source": "twitter",
    "url": "https://example.com"
  },
  "detected_by": "SENTINEL"
}
```

### Intelligence

#### GET `/api/blacklist`

Get all blacklisted addresses.

**Response:**
```json
{
  "blacklist": [
    {
      "address": "ExampleAddress123...",
      "reason": "Confirmed scam",
      "severity": 90,
      "added_at": "2024-01-15T12:00:00"
    }
  ],
  "total": 1
}
```

#### POST `/api/blacklist`

Add an address to the blacklist.

**Request Body:**
```json
{
  "address": "ExampleAddress123...",
  "reason": "Confirmed scam",
  "severity": 90
}
```

#### GET `/api/watchlist`

Get all watched addresses.

#### POST `/api/watchlist`

Add an address to the watchlist.

**Request Body:**
```json
{
  "address": "ExampleAddress123...",
  "label": "High Value Whale",
  "reason": "Monitor for large transactions"
}
```

### Agents

#### GET `/api/agents`

Get statistics for all 16 agents.

**Response:**
```json
{
  "agents": [
    {
      "name": "SENTINEL",
      "role": "Monitor",
      "actions": 1234,
      "threats_detected": 45,
      "last_active": "2024-01-15T12:00:00",
      "status": "active"
    }
  ],
  "total": 16
}
```

### Risk Scoring

#### POST `/api/score`

Calculate risk score for an address.

**Request Body:**
```json
{
  "address": "So11111111111111111111111111111111111111112",
  "threat_type": "token",
  "context": {
    "amount": 1000,
    "transaction_type": "swap"
  }
}
```

**Response:**
```json
{
  "address": "So11111111111111111111111111111111111111112",
  "risk_score": 45.5,
  "risk_level": "MEDIUM",
  "factors": {
    "blacklisted": false,
    "suspicious_patterns": true,
    "age": "new",
    "activity": "high"
  },
  "recommendations": [
    "Use caution when interacting",
    "Limit transaction size"
  ]
}
```

### SwapGuard

#### POST `/api/swap/evaluate`

Evaluate a swap for risks before execution.

**Request Body:**
```json
{
  "user_wallet": "YourWallet...",
  "input_mint": "So11111111111111111111111111111111111111112",
  "output_mint": "TokenMint...",
  "amount": 1.0
}
```

**Response:**
```json
{
  "action": "APPROVE",
  "risk_score": 25,
  "risk_level": "LOW",
  "warnings": [],
  "safe_swap_params": {
    "max_slippage": 0.01,
    "max_position_size": 10.0
  }
}
```

### Evacuator

#### POST `/api/evacuate/register-safe-wallet`

Pre-register a safe wallet for emergency evacuations.

**Request Body:**
```json
{
  "user_wallet": "YourMainWallet...",
  "safe_wallet": "YourColdWallet..."
}
```

#### POST `/api/evacuate/emergency`

🚨 Emergency one-click evacuation.

**Request Body:**
```json
{
  "source_wallet": "CompromisedWallet...",
  "destination_wallet": "SafeWallet...",
  "urgency": "CRITICAL"
}
```

**Response:**
```json
{
  "success": true,
  "total_evacuated_usd": 5000.0,
  "assets_moved": {
    "SOL": 10.0,
    "tokens": 5,
    "nfts": 2
  },
  "approvals_revoked": 3,
  "transactions": ["tx1...", "tx2..."]
}
```

### Network Health

#### GET `/api/network`

Get Solana network health metrics.

**Response:**
```json
{
  "tps": 3500,
  "block_time": 450,
  "congestion_level": 2,
  "status": "healthy",
  "alerts": []
}
```

### Quantum Readiness

#### POST `/api/quantum/assess`

Assess quantum readiness for a wallet.

**Request Body:**
```json
{
  "wallet": "YourWallet..."
}
```

**Response:**
```json
{
  "wallet": "YourWallet...",
  "vulnerability_score": 65,
  "at_risk": true,
  "recommendations": [
    "Migrate to quantum-resistant keys",
    "Use hybrid cryptography"
  ],
  "time_until_vulnerable": "~10 years"
}
```

## WebSocket

### `/ws`

Real-time updates for threats, agent actions, and system events.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

**Message Format:**
```json
{
  "type": "threat_detected",
  "data": {
    "threat_type": "rug_pull",
    "severity": 85,
    "target_address": "..."
  },
  "timestamp": "2024-01-15T12:00:00"
}
```

## Code Examples

### Python

```python
import requests

# Get system status
response = requests.get("http://localhost:8000/api/status")
print(response.json())

# Evaluate a swap
swap_data = {
    "user_wallet": "YourWallet...",
    "input_mint": "So11111111111111111111111111111111111111112",
    "output_mint": "TokenMint...",
    "amount": 1.0
}
response = requests.post("http://localhost:8000/api/swap/evaluate", json=swap_data)
print(response.json())
```

### JavaScript

```javascript
// Get system status
fetch('http://localhost:8000/api/status')
  .then(response => response.json())
  .then(data => console.log(data));

// Evaluate a swap
fetch('http://localhost:8000/api/swap/evaluate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_wallet: 'YourWallet...',
    input_mint: 'So11111111111111111111111111111111111111112',
    output_mint: 'TokenMint...',
    amount: 1.0
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

## OpenAPI/Swagger

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
