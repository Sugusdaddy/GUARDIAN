"""
GUARDIAN Database - SQLite persistence for threats, reasoning, and intelligence
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger()

DB_PATH = Path(__file__).parent.parent.parent / "data" / "guardian.db"


class GuardianDB:
    """
    SQLite database for GUARDIAN persistence.
    Stores threats, reasoning commits, agent stats, and intelligence.
    """
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        self.conn.executescript("""
            -- Threats table
            CREATE TABLE IF NOT EXISTS threats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                threat_type TEXT NOT NULL,
                severity REAL NOT NULL,
                target_address TEXT,
                description TEXT,
                evidence JSON,
                detected_by TEXT NOT NULL,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                resolved_at TIMESTAMP,
                resolution TEXT
            );
            
            -- Reasoning commits (mirrors on-chain data)
            CREATE TABLE IF NOT EXISTS reasoning_commits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                threat_id INTEGER NOT NULL,
                agent_id TEXT NOT NULL,
                reasoning_hash TEXT NOT NULL,
                action_type TEXT NOT NULL,
                commit_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                revealed BOOLEAN DEFAULT FALSE,
                reveal_timestamp TIMESTAMP,
                reasoning_text TEXT,
                tx_signature TEXT,
                FOREIGN KEY (threat_id) REFERENCES threats(id)
            );
            
            -- Agent statistics
            CREATE TABLE IF NOT EXISTS agent_stats (
                agent_id TEXT PRIMARY KEY,
                agent_type TEXT NOT NULL,
                total_scans INTEGER DEFAULT 0,
                threats_detected INTEGER DEFAULT 0,
                true_positives INTEGER DEFAULT 0,
                false_positives INTEGER DEFAULT 0,
                accuracy_score REAL DEFAULT 100.0,
                last_active TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Blacklisted addresses
            CREATE TABLE IF NOT EXISTS blacklist (
                address TEXT PRIMARY KEY,
                reason TEXT,
                added_by TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed_by JSON DEFAULT '[]',
                severity INTEGER DEFAULT 50
            );
            
            -- Watchlist (addresses being monitored)
            CREATE TABLE IF NOT EXISTS watchlist (
                address TEXT PRIMARY KEY,
                label TEXT,
                added_by TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reason TEXT,
                risk_score REAL DEFAULT 0
            );
            
            -- Intelligence patterns (learned from history)
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_data JSON NOT NULL,
                confidence REAL DEFAULT 0,
                occurrences INTEGER DEFAULT 1,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Transaction cache (for analysis)
            CREATE TABLE IF NOT EXISTS tx_cache (
                signature TEXT PRIMARY KEY,
                slot INTEGER,
                block_time INTEGER,
                fee INTEGER,
                from_address TEXT,
                to_address TEXT,
                amount_lamports INTEGER,
                program_ids JSON,
                parsed_data JSON,
                risk_score REAL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Alerts sent
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                threat_id INTEGER,
                channel TEXT NOT NULL,
                message TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivered BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (threat_id) REFERENCES threats(id)
            );
            
            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_threats_status ON threats(status);
            CREATE INDEX IF NOT EXISTS idx_threats_type ON threats(threat_type);
            CREATE INDEX IF NOT EXISTS idx_threats_severity ON threats(severity);
            CREATE INDEX IF NOT EXISTS idx_blacklist_severity ON blacklist(severity);
            CREATE INDEX IF NOT EXISTS idx_tx_cache_time ON tx_cache(block_time);
            CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type);
        """)
        
        self.conn.commit()
        logger.info("Database initialized", path=str(self.db_path))
    
    # ============== THREATS ==============
    
    def insert_threat(self, threat: Dict) -> int:
        """Insert a new threat and return its ID"""
        cursor = self.conn.execute("""
            INSERT INTO threats (threat_type, severity, target_address, description, evidence, detected_by, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            threat["threat_type"],
            threat["severity"],
            threat.get("target_address"),
            threat["description"],
            json.dumps(threat.get("evidence", {})),
            threat["detected_by"],
            threat.get("status", "active")
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_threat(self, threat_id: int) -> Optional[Dict]:
        """Get a threat by ID"""
        row = self.conn.execute("SELECT * FROM threats WHERE id = ?", (threat_id,)).fetchone()
        if row:
            return dict(row)
        return None
    
    def get_active_threats(self, limit: int = 100) -> List[Dict]:
        """Get all active threats"""
        rows = self.conn.execute(
            "SELECT * FROM threats WHERE status = 'active' ORDER BY severity DESC, detected_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    
    def get_threats_by_type(self, threat_type: str, limit: int = 100) -> List[Dict]:
        """Get threats by type"""
        rows = self.conn.execute(
            "SELECT * FROM threats WHERE threat_type = ? ORDER BY detected_at DESC LIMIT ?",
            (threat_type, limit)
        ).fetchall()
        return [dict(r) for r in rows]
    
    def update_threat_status(self, threat_id: int, status: str, resolution: str = None):
        """Update threat status"""
        if status == "resolved":
            self.conn.execute(
                "UPDATE threats SET status = ?, resolved_at = ?, resolution = ? WHERE id = ?",
                (status, datetime.now().isoformat(), resolution, threat_id)
            )
        else:
            self.conn.execute("UPDATE threats SET status = ? WHERE id = ?", (status, threat_id))
        self.conn.commit()
    
    def get_threat_stats(self) -> Dict:
        """Get threat statistics"""
        stats = {}
        
        # Total by status
        rows = self.conn.execute(
            "SELECT status, COUNT(*) as count FROM threats GROUP BY status"
        ).fetchall()
        stats["by_status"] = {r["status"]: r["count"] for r in rows}
        
        # Total by type
        rows = self.conn.execute(
            "SELECT threat_type, COUNT(*) as count FROM threats GROUP BY threat_type ORDER BY count DESC"
        ).fetchall()
        stats["by_type"] = {r["threat_type"]: r["count"] for r in rows}
        
        # Average severity
        row = self.conn.execute("SELECT AVG(severity) as avg_sev FROM threats").fetchone()
        stats["avg_severity"] = row["avg_sev"] or 0
        
        # Recent (last 24h)
        row = self.conn.execute(
            "SELECT COUNT(*) as count FROM threats WHERE detected_at > datetime('now', '-1 day')"
        ).fetchone()
        stats["last_24h"] = row["count"]
        
        return stats
    
    # ============== REASONING ==============
    
    def insert_reasoning_commit(self, commit: Dict) -> int:
        """Insert a reasoning commit"""
        cursor = self.conn.execute("""
            INSERT INTO reasoning_commits 
            (threat_id, agent_id, reasoning_hash, action_type, tx_signature)
            VALUES (?, ?, ?, ?, ?)
        """, (
            commit["threat_id"],
            commit["agent_id"],
            commit["reasoning_hash"],
            commit["action_type"],
            commit.get("tx_signature")
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def reveal_reasoning(self, commit_id: int, reasoning_text: str, tx_signature: str = None):
        """Reveal reasoning for a commit"""
        self.conn.execute("""
            UPDATE reasoning_commits 
            SET revealed = TRUE, reveal_timestamp = ?, reasoning_text = ?, tx_signature = COALESCE(?, tx_signature)
            WHERE id = ?
        """, (datetime.now().isoformat(), reasoning_text, tx_signature, commit_id))
        self.conn.commit()
    
    def get_reasoning_for_threat(self, threat_id: int) -> List[Dict]:
        """Get all reasoning commits for a threat"""
        rows = self.conn.execute(
            "SELECT * FROM reasoning_commits WHERE threat_id = ? ORDER BY commit_timestamp",
            (threat_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    
    # ============== BLACKLIST ==============
    
    def add_to_blacklist(self, address: str, reason: str, added_by: str, severity: int = 50):
        """Add address to blacklist"""
        self.conn.execute("""
            INSERT OR REPLACE INTO blacklist (address, reason, added_by, severity, added_at)
            VALUES (?, ?, ?, ?, ?)
        """, (address, reason, added_by, severity, datetime.now().isoformat()))
        self.conn.commit()
        logger.info(f"Added to blacklist", address=address[:16], severity=severity)
    
    def is_blacklisted(self, address: str) -> bool:
        """Check if address is blacklisted"""
        row = self.conn.execute("SELECT 1 FROM blacklist WHERE address = ?", (address,)).fetchone()
        return row is not None
    
    def get_blacklist(self, min_severity: int = 0) -> List[Dict]:
        """Get blacklisted addresses"""
        rows = self.conn.execute(
            "SELECT * FROM blacklist WHERE severity >= ? ORDER BY severity DESC",
            (min_severity,)
        ).fetchall()
        return [dict(r) for r in rows]
    
    def confirm_blacklist(self, address: str, confirming_agent: str):
        """Add confirmation to a blacklist entry"""
        row = self.conn.execute("SELECT confirmed_by FROM blacklist WHERE address = ?", (address,)).fetchone()
        if row:
            confirmed = json.loads(row["confirmed_by"])
            if confirming_agent not in confirmed:
                confirmed.append(confirming_agent)
                self.conn.execute(
                    "UPDATE blacklist SET confirmed_by = ? WHERE address = ?",
                    (json.dumps(confirmed), address)
                )
                self.conn.commit()
    
    # ============== WATCHLIST ==============
    
    def add_to_watchlist(self, address: str, label: str, added_by: str, reason: str = None):
        """Add address to watchlist"""
        self.conn.execute("""
            INSERT OR REPLACE INTO watchlist (address, label, added_by, reason, added_at)
            VALUES (?, ?, ?, ?, ?)
        """, (address, label, added_by, reason, datetime.now().isoformat()))
        self.conn.commit()
    
    def get_watchlist(self) -> List[Dict]:
        """Get all watched addresses"""
        rows = self.conn.execute("SELECT * FROM watchlist ORDER BY risk_score DESC").fetchall()
        return [dict(r) for r in rows]
    
    def update_risk_score(self, address: str, risk_score: float):
        """Update risk score for watched address"""
        self.conn.execute(
            "UPDATE watchlist SET risk_score = ? WHERE address = ?",
            (risk_score, address)
        )
        self.conn.commit()
    
    # ============== AGENT STATS ==============
    
    def update_agent_stats(self, agent_id: str, agent_type: str, **kwargs):
        """Update agent statistics"""
        self.conn.execute("""
            INSERT INTO agent_stats (agent_id, agent_type, last_active)
            VALUES (?, ?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET last_active = ?
        """, (agent_id, agent_type, datetime.now().isoformat(), datetime.now().isoformat()))
        
        for field, value in kwargs.items():
            if field in ["total_scans", "threats_detected", "true_positives", "false_positives"]:
                self.conn.execute(
                    f"UPDATE agent_stats SET {field} = {field} + ? WHERE agent_id = ?",
                    (value, agent_id)
                )
        
        self.conn.commit()
    
    def get_agent_stats(self, agent_id: str) -> Optional[Dict]:
        """Get stats for an agent"""
        row = self.conn.execute("SELECT * FROM agent_stats WHERE agent_id = ?", (agent_id,)).fetchone()
        return dict(row) if row else None
    
    def get_all_agent_stats(self) -> List[Dict]:
        """Get stats for all agents"""
        rows = self.conn.execute("SELECT * FROM agent_stats ORDER BY threats_detected DESC").fetchall()
        return [dict(r) for r in rows]
    
    # ============== PATTERNS ==============
    
    def record_pattern(self, pattern_type: str, pattern_data: Dict, confidence: float = 0.5):
        """Record or update a pattern"""
        # Check if similar pattern exists
        existing = self.conn.execute(
            "SELECT id, occurrences FROM patterns WHERE pattern_type = ? AND pattern_data = ?",
            (pattern_type, json.dumps(pattern_data))
        ).fetchone()
        
        if existing:
            self.conn.execute("""
                UPDATE patterns 
                SET occurrences = occurrences + 1, last_seen = ?, confidence = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), confidence, existing["id"]))
        else:
            self.conn.execute("""
                INSERT INTO patterns (pattern_type, pattern_data, confidence)
                VALUES (?, ?, ?)
            """, (pattern_type, json.dumps(pattern_data), confidence))
        
        self.conn.commit()
    
    def get_patterns(self, pattern_type: str = None, min_confidence: float = 0) -> List[Dict]:
        """Get learned patterns"""
        if pattern_type:
            rows = self.conn.execute(
                "SELECT * FROM patterns WHERE pattern_type = ? AND confidence >= ? ORDER BY occurrences DESC",
                (pattern_type, min_confidence)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM patterns WHERE confidence >= ? ORDER BY occurrences DESC",
                (min_confidence,)
            ).fetchall()
        return [dict(r) for r in rows]
    
    # ============== TX CACHE ==============
    
    def cache_transaction(self, tx: Dict):
        """Cache a parsed transaction"""
        self.conn.execute("""
            INSERT OR REPLACE INTO tx_cache 
            (signature, slot, block_time, fee, from_address, to_address, amount_lamports, program_ids, parsed_data, risk_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tx["signature"],
            tx.get("slot"),
            tx.get("block_time"),
            tx.get("fee"),
            tx.get("from_address"),
            tx.get("to_address"),
            tx.get("amount_lamports"),
            json.dumps(tx.get("program_ids", [])),
            json.dumps(tx.get("parsed_data", {})),
            tx.get("risk_score", 0)
        ))
        self.conn.commit()
    
    def get_cached_tx(self, signature: str) -> Optional[Dict]:
        """Get cached transaction"""
        row = self.conn.execute("SELECT * FROM tx_cache WHERE signature = ?", (signature,)).fetchone()
        return dict(row) if row else None
    
    def get_high_risk_txs(self, min_risk: float = 50, limit: int = 100) -> List[Dict]:
        """Get high risk transactions"""
        rows = self.conn.execute(
            "SELECT * FROM tx_cache WHERE risk_score >= ? ORDER BY risk_score DESC LIMIT ?",
            (min_risk, limit)
        ).fetchall()
        return [dict(r) for r in rows]
    
    # ============== ALERTS ==============
    
    def record_alert(self, threat_id: int, channel: str, message: str) -> int:
        """Record an alert sent"""
        cursor = self.conn.execute("""
            INSERT INTO alerts (threat_id, channel, message) VALUES (?, ?, ?)
        """, (threat_id, channel, message))
        self.conn.commit()
        return cursor.lastrowid
    
    def mark_alert_delivered(self, alert_id: int):
        """Mark alert as delivered"""
        self.conn.execute("UPDATE alerts SET delivered = TRUE WHERE id = ?", (alert_id,))
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Singleton instance
_db: Optional[GuardianDB] = None


def get_db() -> GuardianDB:
    """Get or create database singleton"""
    global _db
    if _db is None:
        _db = GuardianDB()
    return _db
