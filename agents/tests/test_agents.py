"""
Tests for Solana Immune System Agents
"""
import asyncio
import pytest
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import AgentConfig
from core.base_agent import Threat, Decision


class MockConfig(AgentConfig):
    """Mock config for testing"""
    def __init__(self):
        self.anthropic_api_key = "test-key"
        self.helius_api_key = "test-helius"
        self.solana_rpc_url = "https://api.devnet.solana.com"
        self.wallet_path = "./wallets/guardian-wallet.json"
        self.network = "devnet"
        self.model = "claude-opus-4-20250514"
        self.max_tokens = 2000
        self.scan_interval_seconds = 30
        self.min_threat_confidence = 0.7
        self.require_consensus_threshold = 3
        self.max_memory_entries = 1000
    
    def validate(self):
        return True


@pytest.fixture
def mock_config():
    return MockConfig()


@pytest.fixture
def sample_threat():
    return Threat(
        id=1,
        threat_type="RugPull",
        severity=85,
        target_address="ScamToken111111111111111111111111111111111",
        description="Suspicious token with mint authority enabled",
        evidence={
            "mint_authority": True,
            "top_holder_percentage": 95,
            "liquidity_usd": 500
        },
        detected_by="Scanner"
    )


class TestThreat:
    """Tests for Threat class"""
    
    def test_threat_creation(self, sample_threat):
        assert sample_threat.id == 1
        assert sample_threat.threat_type == "RugPull"
        assert sample_threat.severity == 85
        assert sample_threat.detected_by == "Scanner"
    
    def test_threat_to_dict(self, sample_threat):
        threat_dict = sample_threat.to_dict()
        assert threat_dict["id"] == 1
        assert threat_dict["threat_type"] == "RugPull"
        assert "evidence" in threat_dict


class TestDecision:
    """Tests for Decision class"""
    
    def test_decision_creation(self):
        decision = Decision(
            action="BLOCK",
            confidence=0.9,
            reasoning="High risk token detected",
            requires_consensus=True,
            suggested_agents=["Guardian", "Intel"]
        )
        
        assert decision.action == "BLOCK"
        assert decision.confidence == 0.9
        assert decision.requires_consensus == True
        assert "Guardian" in decision.suggested_agents
    
    def test_decision_to_dict(self):
        decision = Decision(
            action="WARN",
            confidence=0.7,
            reasoning="Medium risk",
            requires_consensus=False
        )
        
        decision_dict = decision.to_dict()
        assert decision_dict["action"] == "WARN"
        assert decision_dict["confidence"] == 0.7


class TestAgentConfig:
    """Tests for AgentConfig"""
    
    def test_mock_config(self, mock_config):
        assert mock_config.network == "devnet"
        assert mock_config.validate() == True


class TestIntegration:
    """Integration tests (require real APIs)"""
    
    @pytest.mark.skip(reason="Requires real API keys")
    @pytest.mark.asyncio
    async def test_swarm_initialization(self, mock_config):
        """Test that swarm initializes with all agents"""
        # Would test full swarm initialization
        pass
    
    @pytest.mark.skip(reason="Requires real API keys")
    @pytest.mark.asyncio
    async def test_threat_detection_flow(self, mock_config, sample_threat):
        """Test full threat detection flow"""
        # Would test detect -> analyze -> commit -> act -> reveal
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
