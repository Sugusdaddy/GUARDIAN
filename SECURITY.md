# Security Policy

## Reporting Vulnerabilities

**DO NOT** create public GitHub issues for security vulnerabilities.

### Contact
- Email: security@solana-immune.system
- PGP Key: [Available on request]

### Bug Bounty Program

We offer bounties for responsible disclosure:

| Severity | Bounty |
|----------|--------|
| Critical | Up to $10,000 |
| High | Up to $5,000 |
| Medium | Up to $1,000 |
| Low | Up to $250 |

### Scope

**In Scope:**
- Smart contracts (programs/)
- Agent logic (agents/)
- API endpoints (app/api/)

**Out of Scope:**
- Third-party dependencies
- Documentation issues
- Social engineering

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: INPUT VALIDATION                                  │
│  ├── All inputs sanitized                                   │
│  ├── Rate limiting on all endpoints                         │
│  └── Schema validation                                      │
│                                                             │
│  Layer 2: HUMAN OVERSIGHT                                   │
│  ├── High-severity actions require human approval           │
│  ├── Emergency stop mechanisms                              │
│  └── Audit trail for all decisions                          │
│                                                             │
│  Layer 3: CONSENSUS REQUIREMENTS                            │
│  ├── Multi-agent voting for critical actions                │
│  ├── Minimum 3 agents must agree                            │
│  └── Coordinator can veto dangerous actions                 │
│                                                             │
│  Layer 4: ON-CHAIN VERIFICATION                             │
│  ├── All reasoning committed before action                  │
│  ├── Hash verification prevents tampering                   │
│  └── Public audit trail on Solana                           │
│                                                             │
│  Layer 5: FALLBACK SYSTEMS                                  │
│  ├── Deterministic rules if AI unavailable                  │
│  ├── Graceful degradation                                   │
│  └── Manual override always available                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Human Oversight

**Critical Actions Requiring Human Approval:**
- Blocking addresses with >$10,000 in assets
- Coordinated responses involving >5 agents
- Actions affecting >100 users
- First-time threat patterns (no historical match)

**Emergency Controls:**
- `EMERGENCY_STOP` environment variable halts all agents
- Admin can pause individual agents via API
- All actions can be reversed within 1 hour

### AI Safety Measures

1. **Deterministic Fallbacks**: If Claude API unavailable, system uses rule-based detection
2. **Confidence Thresholds**: Actions only taken if confidence >70%
3. **False Positive Protection**: Requires 3+ agent agreement for blocking
4. **Rate Limiting**: Max 10 blocking actions per hour
5. **Cooldown Periods**: Same address cannot be re-evaluated for 5 minutes

### Smart Contract Security

- **No upgradeable proxies**: Contracts are immutable after deployment
- **Minimal permissions**: Each contract has single responsibility
- **PDA-based authority**: No admin keys that can be compromised
- **Tested on devnet**: Extensive testing before mainnet

## Audit Status

### Current
- **Internal Review**: Complete
- **Automated Scanning**: Passing (Clippy, cargo-audit)
- **Test Coverage**: See coverage reports

### Planned
- [ ] Professional audit by OtterSec (Q2 2026)
- [ ] Formal verification of critical paths
- [ ] Penetration testing

## Known Limitations

1. **AI Dependency**: System degrades (but doesn't fail) without Claude API
2. **Centralized RPC**: Currently uses Helius (planning to add fallback RPCs)
3. **New Project**: Limited production history

## Incident Response

1. **Detection**: Automated monitoring + community reports
2. **Triage**: Severity assessment within 1 hour
3. **Mitigation**: Emergency stop if needed
4. **Resolution**: Fix deployed within 24 hours for critical issues
5. **Disclosure**: Public post-mortem after resolution

## Compliance

- Open source (MIT License)
- No user funds custody
- Transparent decision-making
- GDPR-compliant logging
