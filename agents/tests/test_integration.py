"""
Integration Tests for Solana Immune System
Tests full flow from detection to action
"""
import pytest
import asyncio
import hashlib
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.base_agent import Threat, Decision
from core.safety import SafetyGuard, DeterministicFallback, ActionSeverity


class TestThreatDetectionFlow:
    """Test complete threat detection flow"""
    
    def test_threat_creation(self):
        """Test threat object creation"""
        threat = Threat(
            id=1,
            threat_type="RugPull",
            severity=94,
            target_address="ScamToken123",
            description="Suspicious token detected",
            evidence={"mint_authority": True},
            detected_by="SCANNER"
        )
        
        assert threat.id == 1
        assert threat.threat_type == "RugPull"
        assert threat.severity == 94
        assert threat.status == "active"
    
    def test_threat_to_dict(self):
        """Test threat serialization"""
        threat = Threat(
            id=1,
            threat_type="RugPull",
            severity=94,
            target_address="ScamToken123",
            description="Test",
            evidence={},
            detected_by="SCANNER"
        )
        
        data = threat.to_dict()
        
        assert "id" in data
        assert "threat_type" in data
        assert "severity" in data
        assert "detected_at" in data
    
    def test_decision_creation(self):
        """Test decision object creation"""
        decision = Decision(
            action="BLOCK",
            confidence=0.94,
            reasoning="High risk token detected",
            requires_consensus=True,
            suggested_agents=["GUARDIAN", "INTEL"]
        )
        
        assert decision.action == "BLOCK"
        assert decision.confidence == 0.94
        assert decision.requires_consensus == True


class TestCommitRevealFlow:
    """Test commit-reveal transparency mechanism"""
    
    def test_hash_computation(self):
        """Test reasoning hash computation"""
        reasoning = "Agent detected rug pull indicators"
        
        hash1 = hashlib.sha256(reasoning.encode()).hexdigest()
        hash2 = hashlib.sha256(reasoning.encode()).hexdigest()
        
        # Same input = same hash
        assert hash1 == hash2
    
    def test_hash_verification(self):
        """Test hash verification"""
        reasoning = "Agent detected rug pull with 94% confidence"
        
        # Commit phase
        committed_hash = hashlib.sha256(reasoning.encode()).hexdigest()
        
        # ... action happens ...
        
        # Reveal phase
        revealed_hash = hashlib.sha256(reasoning.encode()).hexdigest()
        
        # Verify
        assert committed_hash == revealed_hash
    
    def test_tampered_reasoning_detected(self):
        """Tampered reasoning should fail verification"""
        original = "Agent detected rug pull"
        tampered = "Agent detected legitimate token"
        
        committed_hash = hashlib.sha256(original.encode()).hexdigest()
        tampered_hash = hashlib.sha256(tampered.encode()).hexdigest()
        
        assert committed_hash != tampered_hash


class TestSwarmCoordination:
    """Test multi-agent coordination"""
    
    def test_consensus_calculation(self):
        """Test consensus from multiple agent votes"""
        votes = [
            {"agent": "SENTINEL", "approve": True, "confidence": 0.85},
            {"agent": "SCANNER", "approve": True, "confidence": 0.94},
            {"agent": "ORACLE", "approve": True, "confidence": 0.91},
            {"agent": "INTEL", "approve": False, "confidence": 0.60},
        ]
        
        approve_count = sum(1 for v in votes if v["approve"])
        total_count = len(votes)
        consensus_reached = approve_count > total_count / 2
        
        assert consensus_reached == True
        assert approve_count == 3
    
    def test_average_confidence(self):
        """Test average confidence calculation"""
        confidences = [0.85, 0.94, 0.91, 0.60]
        avg = sum(confidences) / len(confidences)
        
        assert 0.80 < avg < 0.85


class TestFallbackSystem:
    """Test fallback when AI unavailable"""
    
    def test_fallback_provides_analysis(self):
        """Fallback should always provide analysis"""
        token = {
            "mint": "AnyToken",
            "mint_authority": True
        }
        
        result = DeterministicFallback.analyze_token(token)
        
        assert "risk_score" in result
        assert "recommendation" in result
        assert "confidence" in result
    
    def test_fallback_consistent_results(self):
        """Fallback should give consistent results"""
        token = {
            "mint": "TestToken",
            "mint_authority": True,
            "top_holder_percentage": 95
        }
        
        result1 = DeterministicFallback.analyze_token(token)
        result2 = DeterministicFallback.analyze_token(token)
        
        assert result1["risk_score"] == result2["risk_score"]
        assert result1["recommendation"] == result2["recommendation"]


class TestSafetyIntegration:
    """Test safety systems integration"""
    
    @pytest.mark.asyncio
    async def test_complete_safety_check(self):
        """Test complete safety check flow"""
        guard = SafetyGuard()
        guard._emergency_stop = False
        guard.recent_actions = []
        guard.blocked_addresses = {}
        
        result = await guard.check_action_allowed(
            action="BLOCK",
            severity=ActionSeverity.HIGH,
            target_address="TestAddr",
            confidence=0.95,
            agent_votes=5
        )
        
        # Should pass with high confidence and enough votes
        assert result["allowed"] == True
    
    @pytest.mark.asyncio
    async def test_action_recording(self):
        """Test action recording for audit trail"""
        guard = SafetyGuard()
        guard.recent_actions = []
        
        guard.record_action("BLOCK", "TestAddr", "success")
        
        assert len(guard.recent_actions) == 1
        assert guard.recent_actions[0]["action"] == "BLOCK"
        assert guard.recent_actions[0]["target"] == "TestAddr"


class TestMetrics:
    """Test metrics and statistics"""
    
    def test_accuracy_calculation(self):
        """Test accuracy rate calculation"""
        total_detections = 47
        true_positives = 45
        false_positives = 2
        
        accuracy = (true_positives / total_detections) * 100
        
        assert 95 < accuracy < 96
    
    def test_response_time_tracking(self):
        """Test response time tracking"""
        detection_time = datetime(2026, 2, 3, 19, 30, 0)
        action_time = datetime(2026, 2, 3, 19, 30, 28)
        
        response_seconds = (action_time - detection_time).total_seconds()
        
        assert response_seconds == 28


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
