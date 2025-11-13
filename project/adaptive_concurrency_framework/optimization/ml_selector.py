"""
ML-based pattern selector for optimal strategy learning.

Uses machine learning to learn optimal strategies from historical
performance data. Optional component that can be enabled for
advanced pattern recognition.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MLPrediction:
    """ML-based prediction for strategy selection."""
    
    strategy: str
    confidence: float
    features: Dict[str, float]
    model_version: str


class MLPatternSelector:
    """
    ML-based pattern selector for strategy selection.
    
    Uses supervised learning to predict optimal strategies:
    - Trains on historical optimization data
    - Predicts optimal strategies for new workloads
    - Continuously learns and improves
    """
    
    def __init__(self, optimization_history: Any, enable_ml: bool = False):
        """
        Initialize ML pattern selector.
        
        Args:
            optimization_history: OptimizationHistory instance
            enable_ml: Whether to enable ML (requires sklearn)
        """
        self.optimization_history = optimization_history
        self.enable_ml = enable_ml
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self._model = None
        self._model_version = "1.0"
        
        if enable_ml:
            try:
                from sklearn.ensemble import RandomForestClassifier
                from sklearn.preprocessing import LabelEncoder
                self._has_sklearn = True
                self._model_class = RandomForestClassifier
                self._label_encoder = LabelEncoder()
            except ImportError:
                self._has_sklearn = False
                self._logger.warning("scikit-learn not available, ML selector disabled")
                self.enable_ml = False
        else:
            self._has_sklearn = False
    
    def train(self) -> bool:
        """
        Train ML model on historical data.
        
        Returns:
            True if training successful
        """
        if not self.enable_ml or not self._has_sklearn:
            return False
        
        history = self.optimization_history.get_history()
        
        if len(history) < 10:
            self._logger.warning("Not enough historical data for training")
            return False
        
        try:
            # Extract features and labels
            features = []
            labels = []
            
            for record in history:
                if record.success is not None:
                    feature_vector = self._extract_features(record.workload_characteristics)
                    features.append(feature_vector)
                    labels.append(record.strategy_selected)
            
            if not features:
                return False
            
            # Train model
            self._model = self._model_class(n_estimators=100, random_state=42)
            self._model.fit(features, labels)
            
            self._logger.info(f"ML model trained on {len(features)} samples")
            return True
            
        except Exception as e:
            self._logger.error(f"ML training error: {e}")
            return False
    
    def predict(self, workload_characteristics: Any) -> Optional[MLPrediction]:
        """
        Predict optimal strategy using ML model.
        
        Args:
            workload_characteristics: Workload characteristics
            
        Returns:
            MLPrediction or None
        """
        if not self.enable_ml or self._model is None:
            return None
        
        try:
            features = self._extract_features(workload_characteristics)
            feature_vector = [features]
            
            # Predict
            strategy = self._model.predict(feature_vector)[0]
            probabilities = self._model.predict_proba(feature_vector)[0]
            
            # Get confidence
            strategy_index = list(self._model.classes_).index(strategy)
            confidence = probabilities[strategy_index]
            
            return MLPrediction(
                strategy=strategy,
                confidence=float(confidence),
                features=features,
                model_version=self._model_version
            )
            
        except Exception as e:
            self._logger.error(f"ML prediction error: {e}")
            return None
    
    def _extract_features(self, workload_characteristics: Any) -> Dict[str, float]:
        """Extract features from workload characteristics."""
        features = {}
        
        if hasattr(workload_characteristics, 'is_cpu_bound'):
            features['is_cpu_bound'] = 1.0 if workload_characteristics.is_cpu_bound else 0.0
        
        if hasattr(workload_characteristics, 'is_io_bound'):
            features['is_io_bound'] = 1.0 if workload_characteristics.is_io_bound else 0.0
        
        if hasattr(workload_characteristics, 'is_mixed'):
            features['is_mixed'] = 1.0 if workload_characteristics.is_mixed else 0.0
        
        if hasattr(workload_characteristics, 'threading_score'):
            features['threading_score'] = workload_characteristics.threading_score
        
        if hasattr(workload_characteristics, 'multiprocessing_score'):
            features['multiprocessing_score'] = workload_characteristics.multiprocessing_score
        
        if hasattr(workload_characteristics, 'asyncio_score'):
            features['asyncio_score'] = workload_characteristics.asyncio_score
        
        # Ensure all features are present
        default_features = {
            'is_cpu_bound': 0.0,
            'is_io_bound': 0.0,
            'is_mixed': 0.0,
            'threading_score': 0.0,
            'multiprocessing_score': 0.0,
            'asyncio_score': 0.0,
        }
        
        for key, default_value in default_features.items():
            if key not in features:
                features[key] = default_value
        
        return features

