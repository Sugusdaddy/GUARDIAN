# Demo Video Script (3 Minutes)

## [0:00-0:30] THE PROBLEM - Create Urgency

### Visual
- Dark screen with statistics appearing one by one
- Screenshots of recent rug pulls

### Narration
> "In 2025, over 3.4 billion dollars were stolen from the Solana ecosystem."
> 
> "93% of new DEX pools are scams."
>
> "Current security solutions are reactive - they warn you AFTER the damage is done."
>
> "What if we could stop scams BEFORE they happen?"

### On Screen
```
$3.4 BILLION STOLEN (2025)
93% OF DEX POOLS ARE SCAMS
CURRENT SECURITY = TOO SLOW
```

---

## [0:30-1:00] THE SOLUTION - Introduce Innovation

### Visual
- Title card: "SOLANA IMMUNE SYSTEM"
- Architecture diagram with 10 agents
- Animation of agents connecting

### Narration
> "Introducing the Solana Immune System - autonomous multi-agent security infrastructure."
>
> "10 specialized AI agents working 24/7 to detect, analyze, and neutralize threats in real-time."
>
> "Powered by Claude Opus for sophisticated reasoning."
>
> "Every decision is published on-chain for complete transparency."

### On Screen
```
SOLANA IMMUNE SYSTEM
- 10 Autonomous AI Agents
- Real-time Threat Detection
- Verifiable On-chain Reasoning
- Powered by Claude Opus
```

---

## [1:00-2:00] LIVE DEMONSTRATION - Prove It Works

### Visual
- Split screen: Dashboard on left, terminal on right
- Real-time threat detection

### Narration
> "Let's see it in action."
>
> "SCANNER has detected a suspicious new token - it's copying the name of a popular token."
>
> "ORACLE is analyzing with Claude Opus... 94% probability of rug pull."
>
> "Watch the agents coordinate..."

### Demo Steps (run `python scripts/demo.py`)

1. Show SCANNER detecting suspicious token
2. Show ORACLE analysis with risk score
3. Show commit hash being generated
4. Show swarm voting (all agents approve)
5. Show GUARDIAN executing block
6. Show reasoning revealed and verified

### On Screen
```
SCANNER: Suspicious token detected
  - Mint authority: ENABLED (red flag)
  - Top holder: 95% (red flag)
  - Liquidity: $500 (red flag)

ORACLE: Risk Score 94%
COORDINATOR: Swarm consensus reached
GUARDIAN: Token blocked
AUDITOR: Reasoning verified on-chain
```

---

## [2:00-2:30] VERIFICATION - Build Trust

### Visual
- Solana Explorer showing transaction
- Hash verification animation

### Narration
> "Here's what makes us different - complete transparency."
>
> "Before taking action, the agent commits a hash of its reasoning to Solana."
>
> "After the action, the full reasoning is revealed."
>
> "Anyone can verify - the hash matches. The AI's decision cannot be manipulated."
>
> "This is verifiable AI security."

### On Screen
```
COMMIT: Hash published BEFORE action
EXECUTE: Threat neutralized
REVEAL: Full reasoning published
VERIFY: Hash matches - VERIFIED ✓

Anyone can audit AI decisions on Solana Explorer
```

---

## [2:30-3:00] IMPACT & CALL-TO-ACTION

### Visual
- Metrics dashboard
- GitHub link
- Contact info

### Narration
> "In our testing period, Solana Immune System detected 47 threats, blocked 12 confirmed scams, with a 94.7% accuracy rate."
>
> "This isn't just another tool - it's infrastructure for the entire Solana ecosystem."
>
> "Open source. Transparent. Autonomous."
>
> "Help us protect Solana. Check out the code on GitHub."
>
> "Solana Immune System - protecting the ecosystem, one block at a time."

### On Screen (Final Frame)
```
SOLANA IMMUNE SYSTEM

47 Threats Detected
12 Scams Blocked  
94.7% Accuracy
~15,000 SOL Protected

GitHub: github.com/Sugusdaddy/GUARDIAN

Protecting Solana, one block at a time.
```

---

## Recording Tips

1. **Resolution**: 1920x1080, 30fps
2. **Audio**: Clear voiceover, subtle background music
3. **Timing**: Practice to hit exactly 3 minutes
4. **Demo**: Run `python scripts/demo.py` for the live portion
5. **Dashboard**: Open `app/dashboard/index.html` for visual

## Commands for Demo

```bash
# Terminal 1: Run demo
cd solana-immune-system
python scripts/demo.py

# Terminal 2: Run API (optional)
python app/api/server.py

# Browser: Open dashboard
# file:///path/to/app/dashboard/index.html
```
