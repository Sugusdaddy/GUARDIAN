"""
Comprehensive tests for Safety Module
Tests human oversight, rate limiting, and fallback systems
"""
import pytest
import asyncio
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.safety import (
    SafetyGuard, SafetyConfig, ActionSeverity,
    DeterministicFallback, get_safety_guard
)


class TestSafetyGuard:
    """Tests for SafetyGuard class"""
    
    @pytest.fixture
    def guard(self):
        config = SafetyConfig(
            min_agents_for_block=3,
            min_confidence_for_action=0.70,
            max_blocks_per_hour=5,
            cooldown_seconds=60
        )
        return SafetyGuard(config)
    
    @pytest.mark.asyncio
    async def test_emergency_stop_blocks_all_actions(self, guard):
        """Emergency stop should block all actions"""
        guard.activate_emergency_stop("test")
        
        result = await guard.check_action_allowed(
            action="WARN",
            severity=ActionSeverity.LOW,
            target_address="test123",
            confidence=0.95
        )
        
        assert result["allowed"] == False
        assert result["reason"] == "emergency_stop_active"
    
    @pytest.mark.asyncio
    async def test_low_confidence_rejected(self, guard):
        """Actions with low confidence should be rejected"""
        result = await guard.check_action_allowed(
            action="BLOCK",
            severity=ActionSeverity.HIGH,
            target_address="test123",
            confidence=0.50  # Below threshold
        )
        
        assert result["allowed"] == False
        assert "confidence_too_low" in result["reason"]
    
    @pytest.mark.asyncio
    async def test_insufficient_consensus_rejected(self, guard):
        """Block actions without enough agent votes should be rejected"""
        result = await guard.check_action_allowed(
            action="BLOCK",
            severity=ActionSeverity.HIGH,
            target_address="test123",
            confidence=0.95,
            agent_votes=2  # Below required 3
        )
        
        assert result["allowed"] == False
        assert "insufficient_consensus" in result["reason"]
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, guard):
        """Rate limiting should block excessive actions"""
        # Record 5 blocks (max allowed)
        for i in range(5):
            guard.record_action("BLOCK", f"addr{i}", "success")
        
        result = await guard.check_action_allowed(
            action="BLOCK",
            severity=ActionSeverity.HIGH,
            target_address="test123",
            confidence=0.95,
            agent_votes=5
        )
        
        assert result["allowed"] == False
        assert "rate_limit_exceeded" in result["reason"]
    
    @pytest.mark.asyncio
    async def test_cooldown_enforcement(self, guard):
        """Same address shouldn't be blocked twice within cooldown"""
        guard.record_action("BLOCK", "repeat_addr", "success")
        
        result = await guard.check_action_allowed(
            action="BLOCK",
            severity=ActionSeverity.HIGH,
            target_address="repeat_addr",
            confidence=0.95,
            agent_votes=5
        )
        
        assert result["allowed"] == False
        assert result["reason"] == "address_in_cooldown"
    
    @pytest.mark.asyncio
    async def test_human_approval_required_for_high_value(self, guard):
        """High-value actions should require human approval"""
        guard.config.require_human_approval_above_value_usd = 5000
        
        result = await guard.check_action_allowed(
            action="BLOCK",
            severity=ActionSeverity.MEDIUM,
            target_address="rich_addr",
            confidence=0.95,
            estimated_value_usd=10000,
            agent_votes=5
        )
        
        assert result["allowed"] == True
        assert result["requires_human_approval"] == True
        assert len(guard.pending_human_approval) == 1
    
    @pytest.mark.asyncio
    async def test_valid_action_passes(self, guard):
        """Valid actions should pass all checks"""
        result = await guard.check_action_allowed(
            action="BLOCK",
            severity=ActionSeverity.MEDIUM,
            target_address="test123",
            confidence=0.95,
            estimated_value_usd=100,
            agent_votes=5
        )
        
        assert result["allowed"] == True
        assert result["requires_human_approval"] == False
    
    def test_approve_pending_action(self, guard):
        """Should be able to approve pending actions"""
        guard.pending_human_approval.append({
            "action": "BLOCK",
            "target": "test",
            "queued_at": datetime.now().isoformat()
        })
        
        assert guard.approve_action(0) == True
        assert len(guard.pending_human_approval) == 0
    
    def test_reject_pending_action(self, guard):
        """Should be able to reject pending actions"""
        guard.pending_human_approval.append({
            "action": "BLOCK",
            "target": "test",
            "queued_at": datetime.now().isoformat()
        })
        
        assert guard.reject_action(0) == True
        assert len(guard.pending_human_approval) == 0


class TestDeterministicFallback:
    """Tests for DeterministicFallback class"""
    
    def test_whitelist_token_ignored(self):
        """Whitelisted tokens should have 0 risk"""
        result = DeterministicFallback.analyze_token({
            "mint": "So11111111111111111111111111111111111111112"  # SOL
        })
        
        assert result["risk_score"] == 0
        assert result["recommendation"] == "IGNORE"
        assert result["confidence"] == 1.0
    
    def test_high_risk_token_blocked(self):
        """High-risk tokens should be recommended for blocking"""
        result = DeterministicFallback.analyze_token({
            "mint": "ScamToken111",
            "mint_authority": True,
            "freeze_authority": True,
            "top_holder_percentage": 95,
            "liquidity_usd": 500,
            "age_hours": 2
        })
        
        assert result["risk_score"] >= 70
        assert result["recommendation"] == "BLOCK"
        assert "mint_authority_enabled" in result["flags"]
        assert "top_holder_above_90_percent" in result["flags"]
    
    def test_medium_risk_token_warned(self):
        """Medium-risk tokens should be warned"""
        result = DeterministicFallback.analyze_token({
            "mint": "SuspiciousToken",
            "mint_authority": True,
            "freeze_authority": True,  # Add more flags for medium risk
            "top_holder_percentage": 50,
            "liquidity_usd": 500,  # Low liquidity
            "age_hours": 48
        })
        
        assert 30 <= result["risk_score"] < 70
        assert result["recommendation"] in ["WARN", "MONITOR"]
    
    def test_low_risk_token_ignored(self):
        """Low-risk tokens should be ignored"""
        result = DeterministicFallback.analyze_token({
            "mint": "LegitToken",
            "mint_authority": False,
            "freeze_authority": False,
            "top_holder_percentage": 20,
            "liquidity_usd": 100000,
            "age_hours": 1000
        })
        
        assert result["risk_score"] < 30
        assert result["recommendation"] in ["IGNORE", "MONITOR"]
    
    def test_large_transaction_flagged(self):
        """Large transactions should be flagged"""
        result = DeterministicFallback.analyze_transaction({
            "amount_sol": 5000,
            "involves_known_scammer": False
        })
        
        assert "large_transfer" in result["flags"]
        assert result["risk_score"] > 0
    
    def test_scammer_transaction_high_risk(self):
        """Transactions with known scammers should be high risk"""
        result = DeterministicFallback.analyze_transaction({
            "amount_sol": 10,
            "involves_known_scammer": True
        })
        
        assert "known_scammer_interaction" in result["flags"]
        assert result["risk_score"] >= 30


class TestIntegration:
    """Integration tests for safety systems"""
    
    @pytest.mark.asyncio
    async def test_full_safety_flow(self):
        """Test complete safety check flow"""
        guard = get_safety_guard()
        
        # Reset state
        guard._emergency_stop = False
        guard.recent_actions = []
        guard.blocked_addresses = {}
        guard.pending_human_approval = []
        
        # Simulate threat detection
        token_data = {
            "mint": "ScamToken",
            "mint_authority": True,
            "top_holder_percentage": 95,
            "liquidity_usd": 100
        }
        
        # Use fallback analysis
        analysis = DeterministicFallback.analyze_token(token_data)
        
        # Check if action is allowed
        result = await guard.check_action_allowed(
            action=analysis["recommendation"],
            severity=ActionSeverity.HIGH if analysis["risk_score"] > 70 else ActionSeverity.MEDIUM,
            target_address=token_data["mint"],
            confidence=analysis["confidence"],
            agent_votes=5
        )
        
        # Should be allowed for blocking
        assert result["allowed"] == True or result["requires_human_approval"] == True
    
    @pytest.mark.asyncio
    async def test_fallback_when_ai_unavailable(self):
        """System should work with deterministic fallback"""
        # Simulate AI unavailable scenario
        token_data = {
            "mint": "UnknownToken",
            "mint_authority": True,
            "freeze_authority": True,
            "top_holder_percentage": 99,
            "liquidity_usd": 50
        }
        
        # Fallback should still provide analysis
        result = DeterministicFallback.analyze_token(token_data)
        
        assert result["risk_score"] > 0
        assert result["recommendation"] in ["IGNORE", "MONITOR", "WARN", "BLOCK"]
        assert result["confidence"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
