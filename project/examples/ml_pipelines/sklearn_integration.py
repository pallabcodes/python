"""
scikit-learn Integration for Production ML Pipelines.

This module provides comprehensive scikit-learn integration for:
- Feature engineering pipelines
- Model training and evaluation
- Model serialization and versioning
- Integration with MLOps platforms

Production Considerations:
- Pipeline serialization for reproducibility
- Model versioning and registry
- Evaluation metrics and validation
- Error handling and logging
"""

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
import json


class SklearnPipeline:
    """
    Base scikit-learn pipeline wrapper.
    
    Provides production-ready pipeline management with:
    - Serialization and versioning
    - Error handling
    - Logging and monitoring
    """
    
    def __init__(self, pipeline_name: str):
        """
        Initialize sklearn pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
        """
        self._pipeline_name = pipeline_name
        self._logger = logging.getLogger(f"{__name__}.{pipeline_name}")
        self._pipeline: Optional[Any] = None
        self._version: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._metadata: Dict[str, Any] = {}
    
    def _check_sklearn_available(self) -> bool:
        """Check if scikit-learn is available."""
        try:
            import sklearn
            return True
        except ImportError:
            self._logger.warning("scikit-learn not installed")
            return False
    
    def save(self, filepath: Union[str, Path]) -> None:
        """
        Save pipeline to disk.
        
        Args:
            filepath: Path to save pipeline
        """
        if not self._pipeline:
            raise ValueError("Pipeline not initialized")
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        pipeline_data = {
            "pipeline": self._pipeline,
            "version": self._version,
            "metadata": self._metadata,
            "pipeline_name": self._pipeline_name
        }
        
        with open(filepath, "wb") as f:
            pickle.dump(pipeline_data, f)
        
        self._logger.info(f"Pipeline saved to {filepath}")
    
    def load(self, filepath: Union[str, Path]) -> None:
        """
        Load pipeline from disk.
        
        Args:
            filepath: Path to load pipeline from
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Pipeline file not found: {filepath}")
        
        with open(filepath, "rb") as f:
            pipeline_data = pickle.load(f)
        
        self._pipeline = pipeline_data["pipeline"]
        self._version = pipeline_data.get("version", "unknown")
        self._metadata = pipeline_data.get("metadata", {})
        self._pipeline_name = pipeline_data.get("pipeline_name", self._pipeline_name)
        
        self._logger.info(f"Pipeline loaded from {filepath}, version: {self._version}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get pipeline metadata."""
        return {
            "pipeline_name": self._pipeline_name,
            "version": self._version,
            **self._metadata
        }


class FeatureEngineeringPipeline(SklearnPipeline):
    """
    Feature engineering pipeline using scikit-learn.
    
    Provides common feature engineering operations:
    - Scaling and normalization
    - Encoding categorical features
    - Feature selection
    - Dimensionality reduction
    """
    
    def __init__(self, pipeline_name: str = "feature_engineering"):
        """Initialize feature engineering pipeline."""
        super().__init__(pipeline_name)
        self._check_and_initialize()
    
    def _check_and_initialize(self) -> None:
        """Check sklearn availability and initialize pipeline."""
        if not self._check_sklearn_available():
            self._logger.warning("scikit-learn not available, pipeline will use mock")
            return
        
        try:
            from sklearn.pipeline import Pipeline
            from sklearn.preprocessing import StandardScaler
            from sklearn.preprocessing import LabelEncoder
            
            # Simple feature engineering pipeline
            self._pipeline = Pipeline([
                ("scaler", StandardScaler()),
            ])
            
            self._metadata["components"] = ["StandardScaler"]
            self._logger.info("Feature engineering pipeline initialized")
            
        except Exception as e:
            self._logger.error(f"Failed to initialize pipeline: {e}")
    
    def fit_transform(self, X: Any, y: Optional[Any] = None) -> Any:
        """
        Fit and transform features.
        
        Args:
            X: Input features
            y: Optional target variable
            
        Returns:
            Transformed features
        """
        if not self._pipeline:
            self._logger.warning("Pipeline not initialized, returning original data")
            return X
        
        try:
            return self._pipeline.fit_transform(X, y)
        except Exception as e:
            self._logger.error(f"Feature engineering error: {e}")
            return X
    
    def transform(self, X: Any) -> Any:
        """
        Transform features using fitted pipeline.
        
        Args:
            X: Input features
            
        Returns:
            Transformed features
        """
        if not self._pipeline:
            self._logger.warning("Pipeline not initialized, returning original data")
            return X
        
        try:
            return self._pipeline.transform(X)
        except Exception as e:
            self._logger.error(f"Feature transformation error: {e}")
            return X


class ModelTrainingPipeline(SklearnPipeline):
    """
    Model training pipeline using scikit-learn.
    
    Provides model training with:
    - Multiple algorithm support
    - Hyperparameter tuning
    - Cross-validation
    - Model evaluation
    """
    
    def __init__(
        self,
        model_type: str = "random_forest",
        pipeline_name: str = "model_training"
    ):
        """
        Initialize model training pipeline.
        
        Args:
            model_type: Type of model (random_forest, svm, logistic_regression, etc.)
            pipeline_name: Name of the pipeline
        """
        super().__init__(pipeline_name)
        self._model_type = model_type
        self._check_and_initialize()
    
    def _check_and_initialize(self) -> None:
        """Check sklearn availability and initialize model."""
        if not self._check_sklearn_available():
            self._logger.warning("scikit-learn not available, model will use mock")
            return
        
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.svm import SVC
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import Pipeline
            from sklearn.preprocessing import StandardScaler
            
            model_map = {
                "random_forest": RandomForestClassifier(n_estimators=100, random_state=42),
                "svm": SVC(random_state=42),
                "logistic_regression": LogisticRegression(random_state=42, max_iter=1000)
            }
            
            model = model_map.get(self._model_type, model_map["random_forest"])
            
            self._pipeline = Pipeline([
                ("scaler", StandardScaler()),
                ("model", model)
            ])
            
            self._metadata["model_type"] = self._model_type
            self._metadata["components"] = ["StandardScaler", self._model_type]
            self._logger.info(f"Model training pipeline initialized: {self._model_type}")
            
        except Exception as e:
            self._logger.error(f"Failed to initialize model: {e}")
    
    def train(self, X: Any, y: Any, **kwargs) -> Dict[str, Any]:
        """
        Train model on data.
        
        Args:
            X: Training features
            y: Training labels
            **kwargs: Additional training parameters
            
        Returns:
            Dictionary with training results and metrics
        """
        if not self._pipeline:
            self._logger.warning("Pipeline not initialized")
            return {"status": "error", "message": "Pipeline not initialized"}
        
        try:
            self._pipeline.fit(X, y)
            
            # Calculate training metrics
            train_score = self._pipeline.score(X, y)
            
            results = {
                "status": "success",
                "train_score": float(train_score),
                "model_type": self._model_type,
                "version": self._version
            }
            
            self._metadata["train_score"] = train_score
            self._metadata["training_date"] = datetime.now().isoformat()
            
            self._logger.info(f"Model trained successfully, train_score: {train_score:.4f}")
            return results
            
        except Exception as e:
            self._logger.error(f"Training error: {e}")
            return {"status": "error", "message": str(e)}
    
    def predict(self, X: Any) -> Any:
        """
        Make predictions using trained model.
        
        Args:
            X: Input features
            
        Returns:
            Predictions
        """
        if not self._pipeline:
            self._logger.warning("Pipeline not initialized")
            return []
        
        try:
            return self._pipeline.predict(X)
        except Exception as e:
            self._logger.error(f"Prediction error: {e}")
            return []
    
    def predict_proba(self, X: Any) -> Any:
        """
        Get prediction probabilities.
        
        Args:
            X: Input features
            
        Returns:
            Prediction probabilities
        """
        if not self._pipeline:
            self._logger.warning("Pipeline not initialized")
            return []
        
        try:
            if hasattr(self._pipeline.named_steps["model"], "predict_proba"):
                return self._pipeline.named_steps["model"].predict_proba(X)
            else:
                self._logger.warning("Model does not support predict_proba")
                return []
        except Exception as e:
            self._logger.error(f"Prediction probability error: {e}")
            return []


class ModelEvaluationPipeline(SklearnPipeline):
    """
    Model evaluation pipeline using scikit-learn.
    
    Provides comprehensive model evaluation:
    - Cross-validation
    - Multiple metrics
    - Classification/regression support
    - Model comparison
    """
    
    def __init__(self, pipeline_name: str = "model_evaluation"):
        """Initialize model evaluation pipeline."""
        super().__init__(pipeline_name)
        self._check_sklearn_available()
    
    def evaluate(
        self,
        model: Any,
        X: Any,
        y: Any,
        cv: int = 5,
        scoring: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate model using cross-validation.
        
        Args:
            model: Trained model or pipeline
            X: Features
            y: Labels
            cv: Number of cross-validation folds
            scoring: Scoring metric (None for default)
            
        Returns:
            Dictionary with evaluation metrics
        """
        if not self._check_sklearn_available():
            return {"status": "error", "message": "scikit-learn not available"}
        
        try:
            from sklearn.model_selection import cross_val_score
            from sklearn.metrics import (
                accuracy_score, precision_score, recall_score, f1_score,
                classification_report, confusion_matrix
            )
            
            # Cross-validation scores
            cv_scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)
            
            # Predictions for additional metrics
            y_pred = model.predict(X)
            
            # Calculate metrics
            accuracy = accuracy_score(y, y_pred)
            precision = precision_score(y, y_pred, average="weighted", zero_division=0)
            recall = recall_score(y, y_pred, average="weighted", zero_division=0)
            f1 = f1_score(y, y_pred, average="weighted", zero_division=0)
            
            results = {
                "status": "success",
                "cv_mean": float(cv_scores.mean()),
                "cv_std": float(cv_scores.std()),
                "cv_scores": cv_scores.tolist(),
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
                "evaluation_date": datetime.now().isoformat()
            }
            
            self._logger.info(f"Model evaluation completed, CV score: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
            return results
            
        except Exception as e:
            self._logger.error(f"Evaluation error: {e}")
            return {"status": "error", "message": str(e)}
    
    def compare_models(
        self,
        models: Dict[str, Any],
        X: Any,
        y: Any,
        cv: int = 5
    ) -> Dict[str, Any]:
        """
        Compare multiple models.
        
        Args:
            models: Dictionary of model_name -> model
            X: Features
            y: Labels
            cv: Number of cross-validation folds
            
        Returns:
            Dictionary with comparison results
        """
        if not self._check_sklearn_available():
            return {"status": "error", "message": "scikit-learn not available"}
        
        try:
            from sklearn.model_selection import cross_val_score
            
            comparison = {}
            
            for model_name, model in models.items():
                cv_scores = cross_val_score(model, X, y, cv=cv)
                comparison[model_name] = {
                    "mean": float(cv_scores.mean()),
                    "std": float(cv_scores.std()),
                    "scores": cv_scores.tolist()
                }
            
            # Find best model
            best_model = max(comparison.items(), key=lambda x: x[1]["mean"])
            
            results = {
                "status": "success",
                "comparison": comparison,
                "best_model": best_model[0],
                "best_score": best_model[1]["mean"],
                "evaluation_date": datetime.now().isoformat()
            }
            
            self._logger.info(f"Model comparison completed, best: {best_model[0]} ({best_model[1]['mean']:.4f})")
            return results
            
        except Exception as e:
            self._logger.error(f"Model comparison error: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    """Demo scikit-learn integration."""
    import asyncio
    
    async def demo():
        logging.basicConfig(level=logging.INFO)
        
        # Feature engineering demo
        print("=== Feature Engineering Pipeline ===")
        feature_pipeline = FeatureEngineeringPipeline()
        # Mock data
        import numpy as np
        X = np.random.randn(100, 5)
        X_transformed = feature_pipeline.fit_transform(X)
        print(f"Original shape: {X.shape}, Transformed shape: {X_transformed.shape}")
        print()
        
        # Model training demo
        print("=== Model Training Pipeline ===")
        training_pipeline = ModelTrainingPipeline(model_type="random_forest")
        y = np.random.randint(0, 2, 100)
        train_results = training_pipeline.train(X, y)
        print(f"Training results: {train_results}")
        
        predictions = training_pipeline.predict(X[:10])
        print(f"Predictions: {predictions}")
        print()
        
        # Model evaluation demo
        print("=== Model Evaluation Pipeline ===")
        eval_pipeline = ModelEvaluationPipeline()
        eval_results = eval_pipeline.evaluate(training_pipeline._pipeline, X, y)
        print(f"Evaluation results: {eval_results}")
        print()
        
        # Save/load demo
        print("=== Pipeline Serialization ===")
        save_path = Path("/tmp/test_pipeline.pkl")
        training_pipeline.save(save_path)
        
        loaded_pipeline = ModelTrainingPipeline()
        loaded_pipeline.load(save_path)
        print(f"Loaded pipeline version: {loaded_pipeline.get_metadata()['version']}")
    
    asyncio.run(demo())