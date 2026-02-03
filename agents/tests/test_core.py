"""
GUARDIAN Core Tests - Database, Embeddings, Scoring
"""
import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import GuardianDB, get_db
from core.embeddings import ThreatEmbedder, ThreatClassifier, RiskScorer, get_scorer
from core.config import config


class TestDatabase:
    """Test database operations"""
    
    @pytest.fixture
    def db(self, tmp_path):
        """Create test database"""
        db_path = tmp_path / "test_guardian.db"
        return GuardianDB(db_path)
    
    def test_insert_threat(self, db):
        """Test threat insertion"""
        threat = {
            "threat_type": "TestThreat",
            "severity": 75.5,
            "target_address": "TestAddr123",
            "description": "Test threat description",
            "evidence": {"test": True},
            "detected_by": "TestAgent"
        }
        
        threat_id = db.insert_threat(threat)
        assert threat_id > 0
        
        # Retrieve
        retrieved = db.get_threat(threat_id)
        assert retrieved is not None
        assert retrieved["threat_type"] == "TestThreat"
        assert retrieved["severity"] == 75.5
    
    def test_active_threats(self, db):
        """Test active threat listing"""
        # Insert multiple threats
        for i in range(5):
            db.insert_threat({
                "threat_type": f"Threat{i}",
                "severity": 50 + i * 10,
                "description": f"Threat {i}",
                "detected_by": "Test"
            })
        
        active = db.get_active_threats(limit=10)
        assert len(active) == 5
        # Should be ordered by severity DESC
        assert active[0]["severity"] >= active[-1]["severity"]
    
    def test_blacklist(self, db):
        """Test blacklist operations"""
        addr = "BlacklistTestAddr"
        
        assert not db.is_blacklisted(addr)
        
        db.add_to_blacklist(addr, "Test reason", "TestAgent", severity=80)
        
        assert db.is_blacklisted(addr)
        
        blacklist = db.get_blacklist()
        assert len(blacklist) == 1
        assert blacklist[0]["address"] == addr
    
    def test_watchlist(self, db):
        """Test watchlist operations"""
        addr = "WatchTestAddr"
        
        db.add_to_watchlist(addr, "TestLabel", "TestAgent", "Suspicious activity")
        
        watchlist = db.get_watchlist()
        assert len(watchlist) == 1
        assert watchlist[0]["address"] == addr
        assert watchlist[0]["label"] == "TestLabel"
    
    def test_reasoning_commit(self, db):
        """Test reasoning commit storage"""
        # First insert a threat
        threat_id = db.insert_threat({
            "threat_type": "Test",
            "severity": 50,
            "description": "Test",
            "detected_by": "Test"
        })
        
        # Insert reasoning commit
        commit_id = db.insert_reasoning_commit({
            "threat_id": threat_id,
            "agent_id": "TestAgent123",
            "reasoning_hash": "abc123hash",
            "action_type": "WARN"
        })
        
        assert commit_id > 0
        
        # Reveal
        db.reveal_reasoning(commit_id, "Full reasoning text here")
        
        # Get reasoning
        reasoning = db.get_reasoning_for_threat(threat_id)
        assert len(reasoning) == 1
        assert reasoning[0]["revealed"] == 1
        assert reasoning[0]["reasoning_text"] == "Full reasoning text here"
    
    def test_patterns(self, db):
        """Test pattern recording"""
        db.record_pattern("Rugpull", {"action": "BLOCK", "severity": 80}, confidence=0.8)
        db.record_pattern("Rugpull", {"action": "BLOCK", "severity": 80}, confidence=0.85)
        
        patterns = db.get_patterns("Rugpull", min_confidence=0.7)
        assert len(patterns) == 1
        assert patterns[0]["occurrences"] == 2
    
    def test_threat_stats(self, db):
        """Test threat statistics"""
        # Insert various threats
        for tt in ["Rugpull", "Rugpull", "Honeypot", "Drainer"]:
            db.insert_threat({
                "threat_type": tt,
                "severity": 70,
                "description": f"{tt} threat",
                "detected_by": "Test"
            })
        
        stats = db.get_threat_stats()
        
        assert stats["by_type"]["Rugpull"] == 2
        assert stats["by_type"]["Honeypot"] == 1
        assert stats["by_status"]["active"] == 4


class TestEmbeddings:
    """Test embedding and ML components"""
    
    def test_embedder_creation(self):
        """Test embedder initializes"""
        embedder = ThreatEmbedder()
        assert embedder is not None
    
    def test_embed_text(self):
        """Test text embedding"""
        embedder = ThreatEmbedder()
        
        if embedder.model is None:
            pytest.skip("No embedding model available")
        
        emb = embedder.embed_text("This is a test threat")
        assert emb is not None
        assert len(emb) == embedder.embedding_dim
    
    def test_embed_threat(self):
        """Test threat embedding"""
        embedder = ThreatEmbedder()
        
        if embedder.model is None:
            pytest.skip("No embedding model available")
        
        threat = {
            "threat_type": "Rugpull",
            "severity": 80,
            "target_address": "TestAddress123",
            "description": "Potential rugpull detected",
            "evidence": {"liquidity_removed": 95}
        }
        
        emb = embedder.embed_threat(threat)
        assert emb is not None
    
    def test_similarity(self):
        """Test similarity calculation"""
        embedder = ThreatEmbedder()
        
        if embedder.model is None:
            pytest.skip("No embedding model available")
        
        emb1 = embedder.embed_text("Rugpull detected, liquidity removed")
        emb2 = embedder.embed_text("Rugpull found, liquidity drained")
        emb3 = embedder.embed_text("Weather is nice today")
        
        sim_similar = embedder.similarity(emb1, emb2)
        sim_different = embedder.similarity(emb1, emb3)
        
        assert sim_similar > sim_different


class TestRiskScorer:
    """Test risk scoring"""
    
    def test_scorer_creation(self):
        """Test scorer initializes"""
        scorer = RiskScorer()
        assert scorer is not None
    
    def test_score_threat(self):
        """Test threat scoring"""
        scorer = get_scorer()
        
        threat = {
            "threat_type": "Rugpull",
            "severity": 80,
            "target_address": "TestAddr",
            "description": "Test rugpull",
            "evidence": {}
        }
        
        result = scorer.score_threat(threat)
        
        assert "final_score" in result
        assert 0 <= result["final_score"] <= 100
        assert "recommendation" in result
        assert result["recommendation"] in ["IGNORE", "MONITOR", "WARN", "COORDINATE", "BLOCK"]
    
    def test_score_with_blacklist(self):
        """Test scoring with blacklist match"""
        scorer = get_scorer()
        
        threat = {
            "threat_type": "Unknown",
            "severity": 50,
            "target_address": "BlacklistedAddr",
            "description": "Test",
            "evidence": {}
        }
        
        # Without blacklist
        result1 = scorer.score_threat(threat)
        
        # With blacklist
        result2 = scorer.score_threat(threat, blacklisted_addresses={"BlacklistedAddr"})
        
        # Blacklist match should increase score
        assert result2["final_score"] > result1["final_score"]
        assert result2["component_scores"]["blacklist_match"] == 100


class TestClassifier:
    """Test threat classifier"""
    
    def test_classifier_creation(self):
        """Test classifier initializes"""
        classifier = ThreatClassifier()
        assert classifier is not None
    
    def test_add_training_sample(self):
        """Test adding training samples"""
        classifier = ThreatClassifier()
        
        threat = {
            "threat_type": "Rugpull",
            "severity": 80,
            "description": "Test rugpull",
            "evidence": {}
        }
        
        initial_count = len(classifier.threat_embeddings)
        classifier.add_training_sample(threat, is_true_positive=True)
        
        # May or may not add depending on embeddings availability
        # Just verify it doesn't crash
    
    def test_predict_risk(self):
        """Test risk prediction"""
        classifier = ThreatClassifier()
        
        threat = {
            "threat_type": "Honeypot",
            "severity": 70,
            "description": "Sell function disabled",
            "evidence": {"sell_disabled": True}
        }
        
        result = classifier.predict_risk(threat)
        
        assert "risk_score" in result
        assert "confidence" in result
        assert "prediction_source" in result


# Integration test
class TestIntegration:
    """Integration tests"""
    
    @pytest.fixture
    def db(self, tmp_path):
        """Create test database"""
        db_path = tmp_path / "test_guardian.db"
        return GuardianDB(db_path)
    
    def test_full_threat_workflow(self, db):
        """Test complete threat processing workflow"""
        scorer = get_scorer()
        
        # 1. Add to blacklist
        db.add_to_blacklist("ScammerAddr123", "Known scammer", "Test", 90)
        
        # 2. Create threat
        threat = {
            "threat_type": "SuspiciousTransfer",
            "severity": 60,
            "target_address": "ScammerAddr123",
            "description": "Large transfer to known scammer",
            "evidence": {"amount_sol": 1000},
            "detected_by": "Sentinel"
        }
        
        # 3. Score threat
        blacklist = set(b["address"] for b in db.get_blacklist())
        score_result = scorer.score_threat(threat, blacklist)
        
        # Should be high risk due to blacklist match
        assert score_result["final_score"] > 70
        
        # 4. Insert threat
        threat_id = db.insert_threat(threat)
        
        # 5. Add reasoning
        commit_id = db.insert_reasoning_commit({
            "threat_id": threat_id,
            "agent_id": "TestAgent",
            "reasoning_hash": "test_hash_123",
            "action_type": "BLOCK"
        })
        
        # 6. Record pattern
        db.record_pattern(
            "SuspiciousTransfer",
            {"action": "BLOCK", "severity": score_result["final_score"]},
            confidence=0.85
        )
        
        # 7. Verify
        patterns = db.get_patterns("SuspiciousTransfer")
        assert len(patterns) == 1
        
        stats = db.get_threat_stats()
        assert stats["by_type"]["SuspiciousTransfer"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
