#!/usr/bin/env python3
"""
GUARDIAN CLI - Interactive command-line interface for testing and operating the system
"""
import asyncio
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich import print as rprint

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent / "agents"))

from agents.core.config import config
from agents.core.database import get_db, GuardianDB

# Try to import ML components (optional)
try:
    from agents.core.embeddings import get_scorer, get_classifier
    HAS_ML = True
except ImportError:
    HAS_ML = False
    get_scorer = lambda: None
    get_classifier = lambda: None

console = Console()
logger = structlog.get_logger()


class GuardianCLI:
    """Interactive CLI for GUARDIAN"""
    
    def __init__(self):
        self.db = get_db()
        self.scorer = get_scorer() if HAS_ML else None
        self.running = True
    
    def print_banner(self):
        """Print welcome banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ ██╗ █████╗ ███╗   ██╗ ║
║  ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║ ║
║  ██║  ███╗██║   ██║███████║██████╔╝██║  ██║██║███████║██╔██╗ ██║ ║
║  ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║██║██╔══██║██║╚██╗██║ ║
║  ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝██║██║  ██║██║ ╚████║ ║
║   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ║
║                                                                  ║
║             Solana Immune System - CLI Interface                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """
        console.print(banner, style="bold cyan")
        console.print(f"  Network: {config.network} | Model: {config.model}\n", style="dim")
    
    def cmd_help(self, args=None):
        """Show help"""
        table = Table(title="Available Commands", show_header=True)
        table.add_column("Command", style="cyan")
        table.add_column("Description")
        
        commands = [
            ("help", "Show this help message"),
            ("status", "Show system status"),
            ("threats [active|all]", "List threats"),
            ("threat <id>", "Show threat details"),
            ("blacklist [list|add|remove]", "Manage blacklist"),
            ("watchlist [list|add]", "Manage watchlist"),
            ("agents", "Show agent statistics"),
            ("patterns", "Show learned patterns"),
            ("score <address>", "Score an address for risk"),
            ("simulate <type>", "Simulate a threat for testing"),
            ("swarm [start|stop|status]", "Control the agent swarm"),
            ("deploy", "Deploy smart contracts to devnet"),
            ("wallet", "Show wallet info and balance"),
            ("airdrop [amount]", "Request devnet SOL airdrop"),
            ("export <file>", "Export database to JSON"),
            ("quit", "Exit CLI"),
        ]
        
        for cmd, desc in commands:
            table.add_row(cmd, desc)
        
        console.print(table)
    
    def cmd_status(self, args=None):
        """Show system status"""
        stats = self.db.get_threat_stats()
        agent_stats = self.db.get_all_agent_stats()
        blacklist = self.db.get_blacklist()
        watchlist = self.db.get_watchlist()
        
        # Main status panel
        status_text = f"""
[bold]Threats:[/bold]
  Active: {stats.get('by_status', {}).get('active', 0)}
  Resolved: {stats.get('by_status', {}).get('resolved', 0)}
  Last 24h: {stats['last_24h']}
  Avg Severity: {stats['avg_severity']:.1f}

[bold]Intelligence:[/bold]
  Blacklisted: {len(blacklist)}
  Watched: {len(watchlist)}
  Agents Active: {len(agent_stats)}

[bold]Configuration:[/bold]
  Network: {config.network}
  RPC: {config.solana_rpc_url[:40]}...
  Model: {config.model}
        """
        
        console.print(Panel(status_text, title="🛡️ GUARDIAN Status", border_style="green"))
    
    def cmd_threats(self, args=None):
        """List threats"""
        filter_type = args[0] if args else "active"
        
        if filter_type == "active":
            threats = self.db.get_active_threats(limit=20)
        else:
            threats = self.db.conn.execute(
                "SELECT * FROM threats ORDER BY detected_at DESC LIMIT 50"
            ).fetchall()
            threats = [dict(t) for t in threats]
        
        if not threats:
            console.print("[yellow]No threats found[/yellow]")
            return
        
        table = Table(title=f"Threats ({filter_type})", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Type")
        table.add_column("Severity", justify="right")
        table.add_column("Target")
        table.add_column("Status")
        table.add_column("Detected")
        
        for t in threats:
            sev = t['severity']
            sev_style = "red" if sev >= 70 else "yellow" if sev >= 40 else "green"
            table.add_row(
                str(t['id']),
                t['threat_type'],
                f"[{sev_style}]{sev:.0f}[/{sev_style}]",
                (t['target_address'] or "")[:12] + "..." if t.get('target_address') else "-",
                t['status'],
                t['detected_at'][:16] if t.get('detected_at') else "-"
            )
        
        console.print(table)
    
    def cmd_threat(self, args):
        """Show threat details"""
        if not args:
            console.print("[red]Usage: threat <id>[/red]")
            return
        
        threat_id = int(args[0])
        threat = self.db.get_threat(threat_id)
        
        if not threat:
            console.print(f"[red]Threat {threat_id} not found[/red]")
            return
        
        # Get reasoning
        reasoning = self.db.get_reasoning_for_threat(threat_id)
        
        # Format evidence
        evidence = threat.get('evidence', '{}')
        if isinstance(evidence, str):
            evidence = json.loads(evidence)
        
        details = f"""
[bold]Type:[/bold] {threat['threat_type']}
[bold]Severity:[/bold] {threat['severity']}
[bold]Status:[/bold] {threat['status']}
[bold]Target:[/bold] {threat.get('target_address') or 'N/A'}
[bold]Detected By:[/bold] {threat['detected_by']}
[bold]Detected At:[/bold] {threat['detected_at']}

[bold]Description:[/bold]
{threat['description']}

[bold]Evidence:[/bold]
{json.dumps(evidence, indent=2)}
        """
        
        console.print(Panel(details, title=f"🚨 Threat #{threat_id}", border_style="red"))
        
        if reasoning:
            console.print("\n[bold]Reasoning Commits:[/bold]")
            for r in reasoning:
                console.print(f"  - {r['action_type']} at {r['commit_timestamp']} (revealed: {r['revealed']})")
    
    def cmd_blacklist(self, args):
        """Manage blacklist"""
        action = args[0] if args else "list"
        
        if action == "list":
            blacklist = self.db.get_blacklist()
            if not blacklist:
                console.print("[yellow]Blacklist is empty[/yellow]")
                return
            
            table = Table(title="Blacklisted Addresses", show_header=True)
            table.add_column("Address")
            table.add_column("Severity", justify="right")
            table.add_column("Reason")
            table.add_column("Added By")
            
            for b in blacklist:
                table.add_row(
                    b['address'][:20] + "...",
                    str(b['severity']),
                    (b['reason'] or "")[:30],
                    b['added_by']
                )
            
            console.print(table)
            
        elif action == "add" and len(args) >= 3:
            address = args[1]
            reason = " ".join(args[2:])
            self.db.add_to_blacklist(address, reason, "CLI", severity=70)
            console.print(f"[green]Added {address[:16]}... to blacklist[/green]")
            
        elif action == "remove" and len(args) >= 2:
            address = args[1]
            self.db.conn.execute("DELETE FROM blacklist WHERE address = ?", (address,))
            self.db.conn.commit()
            console.print(f"[green]Removed {address[:16]}... from blacklist[/green]")
        
        else:
            console.print("[yellow]Usage: blacklist [list|add <address> <reason>|remove <address>][/yellow]")
    
    def cmd_watchlist(self, args):
        """Manage watchlist"""
        action = args[0] if args else "list"
        
        if action == "list":
            watchlist = self.db.get_watchlist()
            if not watchlist:
                console.print("[yellow]Watchlist is empty[/yellow]")
                return
            
            table = Table(title="Watched Addresses", show_header=True)
            table.add_column("Address")
            table.add_column("Label")
            table.add_column("Risk Score", justify="right")
            table.add_column("Reason")
            
            for w in watchlist:
                risk = w['risk_score']
                risk_style = "red" if risk >= 70 else "yellow" if risk >= 40 else "green"
                table.add_row(
                    w['address'][:20] + "...",
                    w['label'] or "-",
                    f"[{risk_style}]{risk:.1f}[/{risk_style}]",
                    (w['reason'] or "")[:30]
                )
            
            console.print(table)
            
        elif action == "add" and len(args) >= 2:
            address = args[1]
            label = args[2] if len(args) > 2 else address[:8]
            self.db.add_to_watchlist(address, label, "CLI")
            console.print(f"[green]Added {address[:16]}... to watchlist[/green]")
        
        else:
            console.print("[yellow]Usage: watchlist [list|add <address> [label]][/yellow]")
    
    def cmd_agents(self, args=None):
        """Show agent statistics"""
        stats = self.db.get_all_agent_stats()
        
        if not stats:
            console.print("[yellow]No agent stats recorded yet[/yellow]")
            return
        
        table = Table(title="Agent Statistics", show_header=True)
        table.add_column("Agent")
        table.add_column("Type")
        table.add_column("Scans", justify="right")
        table.add_column("Threats", justify="right")
        table.add_column("Accuracy", justify="right")
        table.add_column("Last Active")
        
        for a in stats:
            acc = a['accuracy_score']
            acc_style = "green" if acc >= 80 else "yellow" if acc >= 60 else "red"
            table.add_row(
                a['agent_id'][:12] + "...",
                a['agent_type'],
                str(a['total_scans']),
                str(a['threats_detected']),
                f"[{acc_style}]{acc:.0f}%[/{acc_style}]",
                a['last_active'][:16] if a.get('last_active') else "-"
            )
        
        console.print(table)
    
    def cmd_patterns(self, args=None):
        """Show learned patterns"""
        patterns = self.db.get_patterns(min_confidence=0.3)
        
        if not patterns:
            console.print("[yellow]No patterns learned yet[/yellow]")
            return
        
        table = Table(title="Learned Patterns", show_header=True)
        table.add_column("Type")
        table.add_column("Confidence", justify="right")
        table.add_column("Occurrences", justify="right")
        table.add_column("Last Seen")
        
        for p in patterns[:20]:
            conf = p['confidence']
            conf_style = "green" if conf >= 0.7 else "yellow" if conf >= 0.5 else "dim"
            table.add_row(
                p['pattern_type'],
                f"[{conf_style}]{conf:.1%}[/{conf_style}]",
                str(p['occurrences']),
                p['last_seen'][:16] if p.get('last_seen') else "-"
            )
        
        console.print(table)
    
    def cmd_score(self, args):
        """Score an address for risk"""
        if not args:
            console.print("[red]Usage: score <address>[/red]")
            return
        
        address = args[0]
        
        # Check if scorer is available
        if not self.scorer:
            # Fallback to simple scoring
            blacklist = set(b['address'] for b in self.db.get_blacklist())
            is_blacklisted = address in blacklist
            score = 90 if is_blacklisted else 30
            recommendation = "BLOCK" if is_blacklisted else "MONITOR"
            
            details = f"""
[bold]Address:[/bold] {address}

[bold]Risk Score:[/bold] [{"red" if score > 60 else "green"}]{score}/100[/{"red" if score > 60 else "green"}]
[bold]Blacklisted:[/bold] {"Yes" if is_blacklisted else "No"}
[bold]Recommendation:[/bold] {recommendation}

[dim]Note: ML scoring not available. Install numpy and scikit-learn for full scoring.[/dim]
            """
            console.print(Panel(details, title="📊 Risk Assessment (Basic)", border_style="cyan"))
            return
        
        # Create a mock threat for scoring
        threat = {
            "threat_type": "Unknown",
            "severity": 50,
            "target_address": address,
            "description": f"Risk assessment for {address}",
            "evidence": {}
        }
        
        # Get blacklist
        blacklist = set(b['address'] for b in self.db.get_blacklist())
        patterns = self.db.get_patterns(min_confidence=0.5)
        
        result = self.scorer.score_threat(threat, blacklist, patterns)
        
        score = result['final_score']
        score_style = "red" if score >= 70 else "yellow" if score >= 40 else "green"
        
        details = f"""
[bold]Address:[/bold] {address}

[bold]Final Risk Score:[/bold] [{score_style}]{score:.1f}/100[/{score_style}]

[bold]Component Scores:[/bold]
  ML Score: {result['component_scores'].get('ml_score', 0):.1f}
  Severity: {result['component_scores'].get('severity', 0):.1f}
  Blacklist Match: {result['component_scores'].get('blacklist_match', 0):.1f}
  Pattern Match: {result['component_scores'].get('pattern_match', 0):.1f}
  Anomaly: {result['component_scores'].get('anomaly', 0):.1f}

[bold]Recommendation:[/bold] {result['recommendation']}
        """
        
        console.print(Panel(details, title="📊 Risk Assessment", border_style="cyan"))
    
    def cmd_simulate(self, args):
        """Simulate a threat for testing"""
        threat_type = args[0] if args else "SuspiciousTransfer"
        
        threat = {
            "threat_type": threat_type,
            "severity": 75,
            "target_address": "SimuLatedAddr" + "x" * 32,
            "description": f"Simulated {threat_type} threat for testing",
            "evidence": {"simulated": True, "timestamp": datetime.now().isoformat()},
            "detected_by": "CLI-Simulator"
        }
        
        threat_id = self.db.insert_threat(threat)
        console.print(f"[green]Created simulated threat #{threat_id}[/green]")
        
        # Score it
        blacklist = set(b['address'] for b in self.db.get_blacklist())
        result = self.scorer.score_threat(threat, blacklist)
        
        console.print(f"Risk Score: {result['final_score']:.1f} | Recommendation: {result['recommendation']}")
    
    async def cmd_swarm(self, args):
        """Control agent swarm"""
        action = args[0] if args else "status"
        
        if action == "start":
            console.print("[yellow]Starting swarm... (use Ctrl+C to stop)[/yellow]")
            from agents.swarm import SolanaImmuneSystem
            swarm = SolanaImmuneSystem()
            try:
                await swarm.start()
            except KeyboardInterrupt:
                await swarm.stop()
        
        elif action == "status":
            console.print("[yellow]Swarm status check not implemented in CLI mode[/yellow]")
            console.print("Run: python agents/swarm.py")
        
        else:
            console.print("[yellow]Usage: swarm [start|status][/yellow]")
    
    async def cmd_wallet(self, args=None):
        """Show wallet info"""
        try:
            from agents.core.onchain import create_onchain_client
            
            client = await create_onchain_client()
            balance = await client.get_balance()
            
            console.print(Panel(f"""
[bold]Address:[/bold] {client.wallet.pubkey()}
[bold]Balance:[/bold] {balance:.4f} SOL
[bold]Network:[/bold] {client.network}
            """, title="💰 Wallet Info", border_style="green"))
            
            await client.close()
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("[yellow]Make sure wallet.json exists and is configured[/yellow]")
    
    async def cmd_airdrop(self, args):
        """Request devnet airdrop"""
        amount = float(args[0]) if args else 1.0
        
        if config.network != "devnet":
            console.print("[red]Airdrop only available on devnet[/red]")
            return
        
        try:
            from agents.core.onchain import create_onchain_client
            
            console.print(f"[yellow]Requesting {amount} SOL airdrop...[/yellow]")
            
            client = await create_onchain_client()
            sig = await client.request_airdrop(amount)
            
            if sig:
                console.print(f"[green]Airdrop successful! Signature: {sig[:20]}...[/green]")
                balance = await client.get_balance()
                console.print(f"New balance: {balance:.4f} SOL")
            else:
                console.print("[red]Airdrop failed[/red]")
            
            await client.close()
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def cmd_export(self, args):
        """Export database to JSON"""
        if not args:
            console.print("[red]Usage: export <filename>[/red]")
            return
        
        filename = args[0]
        if not filename.endswith('.json'):
            filename += '.json'
        
        data = {
            "exported_at": datetime.now().isoformat(),
            "threats": self.db.get_active_threats(limit=1000),
            "blacklist": self.db.get_blacklist(),
            "watchlist": self.db.get_watchlist(),
            "agent_stats": self.db.get_all_agent_stats(),
            "patterns": self.db.get_patterns(),
            "stats": self.db.get_threat_stats()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        console.print(f"[green]Exported to {filename}[/green]")
    
    async def run_command(self, cmd_line: str):
        """Parse and run a command"""
        parts = cmd_line.strip().split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1:]
        
        commands = {
            "help": self.cmd_help,
            "?": self.cmd_help,
            "status": self.cmd_status,
            "threats": self.cmd_threats,
            "threat": self.cmd_threat,
            "blacklist": self.cmd_blacklist,
            "watchlist": self.cmd_watchlist,
            "agents": self.cmd_agents,
            "patterns": self.cmd_patterns,
            "score": self.cmd_score,
            "simulate": self.cmd_simulate,
            "export": self.cmd_export,
        }
        
        async_commands = {
            "swarm": self.cmd_swarm,
            "wallet": self.cmd_wallet,
            "airdrop": self.cmd_airdrop,
        }
        
        if cmd in ["quit", "exit", "q"]:
            self.running = False
            return
        
        if cmd in commands:
            commands[cmd](args)
        elif cmd in async_commands:
            await async_commands[cmd](args)
        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")
            console.print("Type 'help' for available commands")
    
    async def interactive_loop(self):
        """Main interactive loop"""
        self.print_banner()
        self.cmd_help()
        console.print()
        
        while self.running:
            try:
                cmd = console.input("[bold cyan]guardian>[/bold cyan] ")
                await self.run_command(cmd)
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'quit' to exit[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="GUARDIAN CLI")
    parser.add_argument("command", nargs="*", help="Command to run (or interactive mode if empty)")
    args = parser.parse_args()
    
    cli = GuardianCLI()
    
    if args.command:
        # Run single command
        await cli.run_command(" ".join(args.command))
    else:
        # Interactive mode
        await cli.interactive_loop()


if __name__ == "__main__":
    asyncio.run(main())
