"""
GUARDIAN Embeddings & ML - Real machine learning for threat detection
Uses sentence-transformers for embeddings and sklearn for clustering/classification
"""
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import structlog

logger = structlog.get_logger()

# Try importing ML libraries
try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    logger.warning("sentence-transformers not installed - embeddings disabled")

try:
    from sklearn.cluster import DBSCAN, KMeans
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("sklearn not installed - ML features disabled")


MODEL_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "models"


class ThreatEmbedder:
    """
    Generates embeddings for threats and transactions.
    Uses these for similarity search and pattern detection.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384  # Default for MiniLM
        
        if HAS_EMBEDDINGS:
            try:
                self.model = SentenceTransformer(model_name)
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
                logger.info(f"Loaded embedding model", model=model_name, dim=self.embedding_dim)
            except Exception as e:
                logger.error(f"Failed to load embedding model", error=str(e))
    
    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text"""
        if not self.model:
            return None
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_texts(self, texts: List[str]) -> Optional[np.ndarray]:
        """Generate embeddings for multiple texts"""
        if not self.model:
            return None
        return self.model.encode(texts, convert_to_numpy=True)
    
    def embed_threat(self, threat: Dict) -> Optional[np.ndarray]:
        """Generate embedding for a threat"""
        # Combine threat fields into text
        text_parts = [
            f"Type: {threat.get('threat_type', 'unknown')}",
            f"Description: {threat.get('description', '')}",
            f"Severity: {threat.get('severity', 0)}",
        ]
        
        if threat.get('target_address'):
            text_parts.append(f"Target: {threat['target_address'][:16]}")
        
        if threat.get('evidence'):
            evidence = threat['evidence']
            if isinstance(evidence, str):
                evidence = json.loads(evidence)
            text_parts.append(f"Evidence: {json.dumps(evidence)[:500]}")
        
        text = " | ".join(text_parts)
        return self.embed_text(text)
    
    def embed_transaction(self, tx: Dict) -> Optional[np.ndarray]:
        """Generate embedding for a transaction"""
        text_parts = [
            f"From: {tx.get('from_address', '')[:16] if tx.get('from_address') else 'unknown'}",
            f"To: {tx.get('to_address', '')[:16] if tx.get('to_address') else 'unknown'}",
            f"Amount: {tx.get('amount_lamports', 0) / 1e9:.4f} SOL",
        ]
        
        if tx.get('program_ids'):
            programs = tx['program_ids']
            if isinstance(programs, str):
                programs = json.loads(programs)
            text_parts.append(f"Programs: {', '.join(p[:8] for p in programs[:5])}")
        
        text = " | ".join(text_parts)
        return self.embed_text(text)
    
    def similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity between embeddings"""
        if emb1 is None or emb2 is None:
            return 0.0
        return float(cosine_similarity([emb1], [emb2])[0][0])
    
    def find_similar(
        self,
        query_embedding: np.ndarray,
        embeddings: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Tuple[int, float]]:
        """Find most similar embeddings"""
        if query_embedding is None or embeddings is None or len(embeddings) == 0:
            return []
        
        similarities = cosine_similarity([query_embedding], embeddings)[0]
        
        # Get top-k above threshold
        results = []
        for idx in np.argsort(similarities)[::-1][:top_k]:
            if similarities[idx] >= threshold:
                results.append((int(idx), float(similarities[idx])))
        
        return results


class ThreatClassifier:
    """
    ML classifier for threat detection and risk scoring.
    Uses multiple models for different aspects.
    """
    
    def __init__(self):
        self.embedder = ThreatEmbedder()
        self.scaler = StandardScaler() if HAS_SKLEARN else None
        
        # Models
        self.risk_classifier: Optional[RandomForestClassifier] = None
        self.anomaly_detector: Optional[IsolationForest] = None
        self.pattern_clusterer: Optional[DBSCAN] = None
        
        # Training data
        self.threat_embeddings: List[np.ndarray] = []
        self.threat_labels: List[int] = []  # 0 = false positive, 1 = true positive
        self.threat_types: List[str] = []
        
        # Model paths
        MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.risk_model_path = MODEL_CACHE_DIR / "risk_classifier.pkl"
        self.anomaly_model_path = MODEL_CACHE_DIR / "anomaly_detector.pkl"
        
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models if available"""
        if not HAS_SKLEARN:
            return
        
        if self.risk_model_path.exists():
            try:
                with open(self.risk_model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.risk_classifier = data['model']
                    self.scaler = data.get('scaler', StandardScaler())
                logger.info("Loaded risk classifier model")
            except Exception as e:
                logger.warning(f"Failed to load risk classifier", error=str(e))
        
        if self.anomaly_model_path.exists():
            try:
                with open(self.anomaly_model_path, 'rb') as f:
                    self.anomaly_detector = pickle.load(f)
                logger.info("Loaded anomaly detector model")
            except Exception as e:
                logger.warning(f"Failed to load anomaly detector", error=str(e))
    
    def _save_models(self):
        """Save trained models"""
        if self.risk_classifier:
            with open(self.risk_model_path, 'wb') as f:
                pickle.dump({'model': self.risk_classifier, 'scaler': self.scaler}, f)
        
        if self.anomaly_detector:
            with open(self.anomaly_model_path, 'wb') as f:
                pickle.dump(self.anomaly_detector, f)
    
    def extract_features(self, threat: Dict) -> np.ndarray:
        """Extract numerical features from threat"""
        features = [
            threat.get('severity', 50) / 100.0,
            1.0 if threat.get('target_address') else 0.0,
            len(threat.get('description', '')) / 1000.0,
        ]
        
        # Threat type one-hot
        threat_types = [
            'Rugpull', 'Honeypot', 'Drainer', 'FlashLoan',
            'OracleManipulation', 'Sandwich', 'SuspiciousTransfer',
            'BlacklistedInteraction', 'Unknown'
        ]
        threat_type = threat.get('threat_type', 'Unknown')
        for tt in threat_types:
            features.append(1.0 if threat_type == tt else 0.0)
        
        # Evidence richness
        evidence = threat.get('evidence', {})
        if isinstance(evidence, str):
            try:
                evidence = json.loads(evidence)
            except:
                evidence = {}
        features.append(len(evidence) / 10.0)
        
        return np.array(features)
    
    def add_training_sample(self, threat: Dict, is_true_positive: bool):
        """Add a labeled sample for training"""
        embedding = self.embedder.embed_threat(threat)
        if embedding is not None:
            self.threat_embeddings.append(embedding)
            self.threat_labels.append(1 if is_true_positive else 0)
            self.threat_types.append(threat.get('threat_type', 'Unknown'))
    
    def train_risk_classifier(self, min_samples: int = 20):
        """Train the risk classifier"""
        if not HAS_SKLEARN or len(self.threat_embeddings) < min_samples:
            logger.warning(f"Not enough samples to train ({len(self.threat_embeddings)}/{min_samples})")
            return False
        
        X = np.array(self.threat_embeddings)
        y = np.array(self.threat_labels)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train
        self.risk_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.risk_classifier.fit(X_scaled, y)
        
        self._save_models()
        logger.info(f"Trained risk classifier on {len(y)} samples")
        return True
    
    def train_anomaly_detector(self, normal_threats: List[Dict], contamination: float = 0.1):
        """Train anomaly detector on 'normal' (false positive) threats"""
        if not HAS_SKLEARN or len(normal_threats) < 10:
            return False
        
        embeddings = []
        for threat in normal_threats:
            emb = self.embedder.embed_threat(threat)
            if emb is not None:
                embeddings.append(emb)
        
        if len(embeddings) < 10:
            return False
        
        X = np.array(embeddings)
        
        self.anomaly_detector = IsolationForest(
            contamination=contamination,
            random_state=42
        )
        self.anomaly_detector.fit(X)
        
        self._save_models()
        logger.info(f"Trained anomaly detector on {len(embeddings)} samples")
        return True
    
    def predict_risk(self, threat: Dict) -> Dict[str, Any]:
        """Predict risk score for a threat"""
        result = {
            "risk_score": 50.0,
            "confidence": 0.0,
            "is_anomaly": None,
            "similar_threats": [],
            "prediction_source": "default"
        }
        
        embedding = self.embedder.embed_threat(threat)
        
        # Use classifier if available
        if self.risk_classifier and embedding is not None:
            X = self.scaler.transform([embedding])
            proba = self.risk_classifier.predict_proba(X)[0]
            result["risk_score"] = float(proba[1]) * 100  # P(true positive)
            result["confidence"] = float(max(proba))
            result["prediction_source"] = "classifier"
        
        # Check for anomaly
        if self.anomaly_detector and embedding is not None:
            score = self.anomaly_detector.decision_function([embedding])[0]
            result["is_anomaly"] = score < 0
            result["anomaly_score"] = float(score)
        
        # Find similar historical threats
        if embedding is not None and len(self.threat_embeddings) > 0:
            similar = self.embedder.find_similar(
                embedding,
                np.array(self.threat_embeddings),
                top_k=3,
                threshold=0.7
            )
            result["similar_threats"] = [
                {"index": idx, "similarity": sim, "type": self.threat_types[idx]}
                for idx, sim in similar
            ]
        
        return result
    
    def cluster_threats(self, threats: List[Dict], eps: float = 0.3, min_samples: int = 2) -> Dict[str, Any]:
        """Cluster threats to find patterns"""
        if not HAS_SKLEARN or len(threats) < min_samples:
            return {"clusters": [], "noise": list(range(len(threats)))}
        
        embeddings = []
        for threat in threats:
            emb = self.embedder.embed_threat(threat)
            if emb is not None:
                embeddings.append(emb)
            else:
                embeddings.append(np.zeros(self.embedder.embedding_dim))
        
        X = np.array(embeddings)
        
        clusterer = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
        labels = clusterer.fit_predict(X)
        
        # Group by cluster
        clusters = {}
        noise = []
        for idx, label in enumerate(labels):
            if label == -1:
                noise.append(idx)
            else:
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(idx)
        
        return {
            "clusters": [{"id": k, "members": v} for k, v in clusters.items()],
            "noise": noise,
            "n_clusters": len(clusters)
        }


class RiskScorer:
    """
    Combines multiple signals for comprehensive risk scoring.
    """
    
    def __init__(self):
        self.classifier = ThreatClassifier()
        
        # Risk weights for different factors
        self.weights = {
            "ml_score": 0.3,
            "severity": 0.2,
            "blacklist_match": 0.25,
            "pattern_match": 0.15,
            "anomaly": 0.1
        }
    
    def score_threat(
        self,
        threat: Dict,
        blacklisted_addresses: set = None,
        known_patterns: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Compute comprehensive risk score (0-100).
        """
        scores = {}
        
        # ML prediction
        ml_result = self.classifier.predict_risk(threat)
        scores["ml_score"] = ml_result["risk_score"]
        
        # Raw severity
        scores["severity"] = threat.get("severity", 50)
        
        # Blacklist check
        target = threat.get("target_address", "")
        if blacklisted_addresses and target in blacklisted_addresses:
            scores["blacklist_match"] = 100
        else:
            scores["blacklist_match"] = 0
        
        # Pattern matching
        scores["pattern_match"] = 0
        if known_patterns:
            threat_type = threat.get("threat_type", "")
            for pattern in known_patterns:
                if pattern.get("pattern_type") == threat_type:
                    scores["pattern_match"] = min(100, pattern.get("confidence", 0) * 100)
                    break
        
        # Anomaly score
        if ml_result.get("is_anomaly"):
            scores["anomaly"] = 80
        else:
            scores["anomaly"] = 20
        
        # Weighted combination
        final_score = sum(
            scores.get(k, 0) * v 
            for k, v in self.weights.items()
        )
        
        return {
            "final_score": min(100, max(0, final_score)),
            "component_scores": scores,
            "ml_details": ml_result,
            "recommendation": self._get_recommendation(final_score)
        }
    
    def _get_recommendation(self, score: float) -> str:
        """Get action recommendation based on score"""
        if score >= 80:
            return "BLOCK"
        elif score >= 60:
            return "COORDINATE"
        elif score >= 40:
            return "WARN"
        elif score >= 20:
            return "MONITOR"
        else:
            return "IGNORE"


# Singleton instances
_embedder: Optional[ThreatEmbedder] = None
_classifier: Optional[ThreatClassifier] = None
_scorer: Optional[RiskScorer] = None


def get_embedder() -> ThreatEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = ThreatEmbedder()
    return _embedder


def get_classifier() -> ThreatClassifier:
    global _classifier
    if _classifier is None:
        _classifier = ThreatClassifier()
    return _classifier


def get_scorer() -> RiskScorer:
    global _scorer
    if _scorer is None:
        _scorer = RiskScorer()
    return _scorer
