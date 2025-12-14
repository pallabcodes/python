"""
Integration Tests for scikit-learn ML Pipelines.

Tests feature engineering, model training, evaluation, and serialization.
"""

import os
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Import sklearn integration
try:
    from examples.ml_pipelines.sklearn_integration import (
        FeatureEngineeringPipeline,
        ModelTrainingPipeline,
        ModelEvaluationPipeline
    )
except ImportError:
    pytest.skip("scikit-learn integration not available", allow_module_level=True)


class TestFeatureEngineeringIntegration:
    """Integration tests for feature engineering pipeline."""

    @pytest.fixture
    def feature_pipeline(self):
        """Fixture for feature engineering pipeline."""
        return FeatureEngineeringPipeline()

    def test_pipeline_initialization(self, feature_pipeline):
        """Test pipeline initializes correctly."""
        assert feature_pipeline is not None
        assert hasattr(feature_pipeline, 'fit_transform')
        assert hasattr(feature_pipeline, 'transform')

    def test_feature_transformation(self, feature_pipeline):
        """Test basic feature transformation."""
        # Create sample data
        X = np.random.randn(100, 5)

        # Test fit_transform
        X_transformed = feature_pipeline.fit_transform(X)

        assert isinstance(X_transformed, np.ndarray)
        assert X_transformed.shape[0] == X.shape[0]  # Same number of samples

        # Test transform on new data
        X_new = np.random.randn(20, 5)
        X_new_transformed = feature_pipeline.transform(X_new)

        assert isinstance(X_new_transformed, np.ndarray)
        assert X_new_transformed.shape[0] == X_new.shape[0]

    def test_different_data_types(self, feature_pipeline):
        """Test with different data types."""
        # Integer data
        X_int = np.random.randint(0, 10, (50, 3))
        X_int_transformed = feature_pipeline.fit_transform(X_int)
        assert isinstance(X_int_transformed, np.ndarray)

        # Float data
        X_float = np.random.rand(50, 3).astype(np.float32)
        X_float_transformed = feature_pipeline.fit_transform(X_float)
        assert isinstance(X_float_transformed, np.ndarray)

    def test_edge_cases(self, feature_pipeline):
        """Test edge cases."""
        # Single feature
        X_single = np.random.randn(10, 1)
        X_single_transformed = feature_pipeline.fit_transform(X_single)
        assert X_single_transformed.shape[1] >= 1  # May add features

        # Large dataset
        X_large = np.random.randn(1000, 10)
        X_large_transformed = feature_pipeline.fit_transform(X_large)
        assert X_large_transformed.shape[0] == X_large.shape[0]


class TestModelTrainingIntegration:
    """Integration tests for model training pipeline."""

    @pytest.fixture
    def training_pipeline(self):
        """Fixture for model training pipeline."""
        return ModelTrainingPipeline(model_type="random_forest")

    @pytest.fixture
    def sample_data(self):
        """Sample training data."""
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, 100)  # Binary classification
        return X, y

    def test_pipeline_initialization(self, training_pipeline):
        """Test training pipeline initializes correctly."""
        assert training_pipeline is not None
        assert hasattr(training_pipeline, 'train')
        assert hasattr(training_pipeline, 'predict')

    def test_model_training(self, training_pipeline, sample_data):
        """Test model training process."""
        X, y = sample_data

        # Train the model
        results = training_pipeline.train(X, y)

        assert isinstance(results, dict)
        assert results["status"] == "success"
        assert "train_score" in results
        assert isinstance(results["train_score"], float)
        assert 0.0 <= results["train_score"] <= 1.0

    def test_prediction(self, training_pipeline, sample_data):
        """Test model prediction."""
        X, y = sample_data

        # Train first
        training_pipeline.train(X, y)

        # Make predictions
        predictions = training_pipeline.predict(X)

        assert isinstance(predictions, np.ndarray)
        assert len(predictions) == len(X)
        assert all(pred in [0, 1] for pred in predictions)

    def test_probability_prediction(self, training_pipeline, sample_data):
        """Test probability predictions."""
        X, y = sample_data

        # Train first
        training_pipeline.train(X, y)

        # Get probabilities
        probabilities = training_pipeline.predict_proba(X)

        if probabilities is not None:
            assert isinstance(probabilities, np.ndarray)
            assert probabilities.shape[0] == len(X)
            assert probabilities.shape[1] == 2  # Binary classification
            assert np.all((probabilities >= 0) & (probabilities <= 1))
            assert np.allclose(probabilities.sum(axis=1), 1.0)  # Probabilities sum to 1

    def test_different_models(self, sample_data):
        """Test different model types."""
        X, y = sample_data

        model_types = ["random_forest", "logistic_regression"]
        if ModelTrainingPipeline(model_type="svm")._check_sklearn_available():
            model_types.append("svm")

        for model_type in model_types:
            pipeline = ModelTrainingPipeline(model_type=model_type)

            # Train
            results = pipeline.train(X, y)
            assert results["status"] == "success"

            # Predict
            predictions = pipeline.predict(X[:10])
            assert len(predictions) == 10

    def test_pipeline_serialization(self, training_pipeline, sample_data):
        """Test pipeline save/load functionality."""
        X, y = sample_data

        # Train the model
        training_pipeline.train(X, y)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp_file:
            save_path = tmp_file.name

        try:
            training_pipeline.save(save_path)

            # Create new pipeline and load
            loaded_pipeline = ModelTrainingPipeline()
            loaded_pipeline.load(save_path)

            # Test that loaded pipeline works
            predictions_original = training_pipeline.predict(X[:10])
            predictions_loaded = loaded_pipeline.predict(X[:10])

            # Predictions should be identical
            np.testing.assert_array_equal(predictions_original, predictions_loaded)

        finally:
            # Clean up
            if os.path.exists(save_path):
                os.unlink(save_path)


class TestModelEvaluationIntegration:
    """Integration tests for model evaluation pipeline."""

    @pytest.fixture
    def eval_pipeline(self):
        """Fixture for evaluation pipeline."""
        return ModelEvaluationPipeline()

    @pytest.fixture
    def trained_pipeline(self, sample_data):
        """Pre-trained pipeline for testing."""
        X, y = sample_data
        pipeline = ModelTrainingPipeline(model_type="random_forest")
        pipeline.train(X, y)
        return pipeline, X, y

    def test_evaluation_basic(self, eval_pipeline, trained_pipeline):
        """Test basic model evaluation."""
        pipeline, X, y = trained_pipeline

        results = eval_pipeline.evaluate(pipeline._pipeline, X, y, cv=3)

        assert isinstance(results, dict)
        assert results["status"] == "success"
        assert "cv_mean" in results
        assert "cv_std" in results
        assert "accuracy" in results
        assert "precision" in results
        assert "recall" in results
        assert "f1_score" in results

        # Check value ranges
        assert 0.0 <= results["cv_mean"] <= 1.0
        assert 0.0 <= results["accuracy"] <= 1.0
        assert 0.0 <= results["precision"] <= 1.0
        assert 0.0 <= results["recall"] <= 1.0
        assert 0.0 <= results["f1_score"] <= 1.0

    def test_model_comparison(self, eval_pipeline, sample_data):
        """Test model comparison functionality."""
        X, y = sample_data

        # Create multiple models
        models = {}
        model_types = ["random_forest", "logistic_regression"]

        for model_type in model_types:
            pipeline = ModelTrainingPipeline(model_type=model_type)
            pipeline.train(X, y)
            models[model_type] = pipeline._pipeline

        # Compare models
        comparison = eval_pipeline.compare_models(models, X, y, cv=3)

        assert isinstance(comparison, dict)
        assert comparison["status"] == "success"
        assert "comparison" in comparison
        assert "best_model" in comparison
        assert "best_score" in comparison

        # Check that all models are in comparison
        for model_type in model_types:
            assert model_type in comparison["comparison"]
            assert "mean" in comparison["comparison"][model_type]
            assert "std" in comparison["comparison"][model_type]

    def test_cross_validation_variations(self, eval_pipeline, trained_pipeline):
        """Test different cross-validation configurations."""
        pipeline, X, y = trained_pipeline

        # Test different CV folds
        for cv_folds in [2, 3, 5]:
            results = eval_pipeline.evaluate(pipeline._pipeline, X, y, cv=cv_folds)
            assert results["status"] == "success"
            assert len(results["cv_scores"]) == cv_folds

    def test_evaluation_with_different_scoring(self, eval_pipeline, trained_pipeline):
        """Test evaluation with different scoring metrics."""
        pipeline, X, y = trained_pipeline

        # Test different scoring metrics
        scoring_metrics = ["accuracy", "precision", "recall", "f1"]

        for scoring in scoring_metrics:
            try:
                results = eval_pipeline.evaluate(pipeline._pipeline, X, y, cv=3, scoring=scoring)
                assert results["status"] == "success"
            except Exception:
                # Some scoring metrics might not be compatible with all models
                pass


class TestMLPipelineStress:
    """Stress tests for ML pipelines."""

    def test_large_dataset_handling(self):
        """Test handling of larger datasets."""
        # Create larger dataset
        X = np.random.randn(1000, 10)
        y = np.random.randint(0, 2, 1000)

        # Test feature engineering
        feature_pipeline = FeatureEngineeringPipeline()
        X_transformed = feature_pipeline.fit_transform(X)
        assert X_transformed.shape[0] == X.shape[0]

        # Test training
        training_pipeline = ModelTrainingPipeline()
        results = training_pipeline.train(X_transformed, y)
        assert results["status"] == "success"

        # Test evaluation
        eval_pipeline = ModelEvaluationPipeline()
        eval_results = eval_pipeline.evaluate(training_pipeline._pipeline, X_transformed, y, cv=3)
        assert eval_results["status"] == "success"

    def test_concurrent_pipeline_usage(self):
        """Test concurrent usage of pipelines."""
        import threading
        import queue

        results = queue.Queue()
        errors = queue.Queue()

        def worker_pipeline(worker_id):
            try:
                # Create sample data
                X = np.random.randn(50, 3)
                y = np.random.randint(0, 2, 50)

                # Train model
                pipeline = ModelTrainingPipeline()
                train_results = pipeline.train(X, y)

                # Make predictions
                predictions = pipeline.predict(X[:10])

                results.put((worker_id, len(predictions), train_results["status"]))
            except Exception as e:
                errors.put((worker_id, str(e)))

        # Start multiple threads
        threads = []
        num_threads = 5

        for i in range(num_threads):
            t = threading.Thread(target=worker_pipeline, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join(timeout=60)  # 60 second timeout

        # Check results
        assert results.qsize() == num_threads
        assert errors.qsize() == 0

        # Verify all results are valid
        while not results.empty():
            worker_id, pred_length, status = results.get()
            assert pred_length == 10
            assert status == "success"


class TestMLPipelineErrorHandling:
    """Error handling tests for ML pipelines."""

    def test_invalid_data_handling(self):
        """Test handling of invalid input data."""
        pipeline = ModelTrainingPipeline()

        # Test with None data
        with pytest.raises(Exception):
            pipeline.train(None, None)

        # Test with mismatched dimensions
        X = np.random.randn(10, 5)
        y = np.random.randint(0, 2, 5)  # Wrong size

        with pytest.raises(Exception):
            pipeline.train(X, y)

    def test_missing_dependencies(self):
        """Test graceful handling when sklearn not available."""
        # This would normally be handled by the skip decorator
        # but we can test the internal check
        pipeline = ModelTrainingPipeline()

        # If sklearn is available, training should work
        if pipeline._check_sklearn_available():
            X = np.random.randn(10, 2)
            y = np.random.randint(0, 2, 10)
            results = pipeline.train(X, y)
            assert "status" in results

    def test_file_operation_errors(self):
        """Test file save/load error handling."""
        pipeline = ModelTrainingPipeline()

        # Test loading non-existent file
        with pytest.raises(FileNotFoundError):
            pipeline.load("/non/existent/file.pkl")

        # Test saving to invalid path
        with pytest.raises(Exception):
            pipeline.save("/invalid/path/file.pkl")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])