"""
Advanced integration tests for HTTP fetcher.

This module contains integration tests for complex scenarios
and end-to-end functionality testing.
"""

import pytest
from unittest.mock import Mock, patch

from .fetcher_stage_core import HttpFetcherStage
from .fetcher_stage_batch import BatchHttpFetcherStage


class TestIntegrationScenarios:
    """Tests for integration scenarios and edge cases."""

    def test_single_vs_batch_processing(self):
        """Test single request vs batch processing."""
        # Single request processing
        single_stage = HttpFetcherStage(name="SingleFetcher")

        # Mock successful response
        import time
        mock_response = type('MockResponse', (), {
            'status_code': 200,
            'content': b'{"result": "ok"}',
            'headers': {"content-type": "application/json"},
            'url': "https://api.example.com/test",
            'elapsed': 0.1,
            'request_time': time.time()
        })()

        with patch('http_fetcher.http_client_impl.HttpClient.request', return_value=mock_response):
            single_result = single_stage.transform({"url": "https://api.example.com/test"})
            assert single_result["status_code"] == 200

        # Batch processing
        batch_stage = BatchHttpFetcherStage(name="BatchFetcher", max_concurrent=2)
        batch_stage._fetcher_stage = single_stage

        batch_requests = [
            {"url": "https://api.example.com/1"},
            {"url": "https://api.example.com/2"}
        ]

        batch_result = batch_stage.transform(batch_requests)
        assert len(batch_result) == 2

    def test_mixed_success_failure_batch(self):
        """Test batch with mix of success and failure responses."""
        batch_stage = BatchHttpFetcherStage(name="MixedBatch", max_concurrent=2)

        # Mock fetcher with mixed results
        mock_fetcher = Mock()
        mock_fetcher.transform.side_effect = [
            {"status_code": 200, "data": "success1"},
            {"error": True, "error_message": "Connection failed"},
            {"status_code": 200, "data": "success2"}
        ]
        batch_stage._fetcher_stage = mock_fetcher

        batch_requests = [
            {"url": "https://api.example.com/1"},
            {"url": "https://api.example.com/2"},
            {"url": "https://api.example.com/3"}
        ]

        results = batch_stage.transform(batch_requests)

        assert len(results) == 3
        assert results[0]["data"] == "success1"
        assert results[1]["error"] is True
        assert results[2]["data"] == "success2"


class TestPipelineIntegration:
    """Tests for pipeline integration scenarios."""

    def test_fetcher_in_pipeline_context(self):
        """Test fetcher stage in full pipeline context."""
        from ..pipeline_core.runner import PipelineRunner
        from ..pipeline_core.stage_types import TransformStage

        class ResultProcessor(TransformStage):
            def transform(self, data):
                if isinstance(data, dict) and "status_code" in data:
                    return f"Processed: {data['status_code']}"
                return data

        # Create pipeline with fetcher
        fetcher = HttpFetcherStage(name="PipelineFetcher", requests_per_second=1.0)
        processor = ResultProcessor(name="Processor")

        pipeline = PipelineRunner([fetcher, processor])

        # Mock successful response
        import time
        mock_response = type('MockResponse', (), {
            'status_code': 200,
            'content': b'{"result": "ok"}',
            'headers': {"content-type": "application/json"},
            'url': "https://api.example.com/test",
            'elapsed': 0.1,
            'request_time': time.time()
        })()

        with patch('http_fetcher.http_client_impl.HttpClient.request', return_value=mock_response):
            input_messages = [{"url": "https://api.example.com/test"}]

            results = pipeline.run_pipeline(input_messages, timeout=10.0)

            assert results["success"] is True
            assert len(input_messages) == 1

    def test_error_propagation_in_pipeline(self):
        """Test error propagation through pipeline stages."""
        from ..pipeline_core.runner import PipelineRunner
        from ..pipeline_core.stage_types import TransformStage

        class ErrorHandler(TransformStage):
            def transform(self, data):
                if isinstance(data, dict) and data.get("error"):
                    return f"Handled error: {data['error_message']}"
                return data

        # Create pipeline with error handling
        fetcher = HttpFetcherStage(name="ErrorFetcher", max_retries=0)
        error_handler = ErrorHandler(name="ErrorHandler")

        pipeline = PipelineRunner([fetcher, error_handler])

        # Mock failed response
        with patch('http_fetcher.http_client_impl.HttpClient.request', side_effect=Exception("Network error")):
            input_messages = [{"url": "https://api.example.com/fail"}]

            results = pipeline.run_pipeline(input_messages, timeout=5.0)

            # Pipeline should complete but with errors
            assert "errors" in results or results["success"] is False


if __name__ == "__main__":
    """Run integration tests when executed directly."""
    pytest.main([__file__, "-v"])

