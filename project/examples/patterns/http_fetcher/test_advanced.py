"""
Advanced unit tests for HTTP fetcher functionality.

This module contains advanced tests for pipeline stages,
batch processing, and complex scenarios.
"""

import pytest
from unittest.mock import Mock, patch

from .fetcher_stage import HttpFetcherStage, BatchHttpFetcherStage


class TestHttpFetcherStage:
    """Tests for HTTP fetcher pipeline stage."""

    def test_fetcher_stage_initialization(self):
        """Test fetcher stage initialization."""
        stage = HttpFetcherStage(
            name="TestFetcher",
            base_url="https://api.example.com",
            requests_per_second=5.0,
            max_retries=2
        )

        assert stage.name == "TestFetcher"
        assert stage.base_url == "https://api.example.com"
        assert stage.requests_per_second == 5.0
        assert stage.max_retries == 2

    def test_request_params_extraction(self):
        """Test extraction of request parameters."""
        stage = HttpFetcherStage(name="TestFetcher")

        # Test string URL
        params = stage._extract_request_params("https://example.com")
        assert params["url"] == "https://example.com"
        assert params["method"] == "GET"

        # Test dict with parameters
        request_dict = {
            "url": "/api/data",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "data": '{"key": "value"}'
        }
        params = stage._extract_request_params(request_dict)
        assert params["url"] == "/api/data"
        assert params["method"] == "POST"
        assert params["headers"]["Content-Type"] == "application/json"

    @patch('http_fetcher.http_client.HttpClient.request')
    def test_successful_fetch(self, mock_request):
        """Test successful HTTP fetch."""
        import time
        # Mock successful response
        mock_response = HttpResponse(
            status_code=200,
            content=b'{"result": "success"}',
            headers={"content-type": "application/json"},
            url="https://api.example.com/data",
            elapsed=0.5,
            request_time=time.time()
        )
        mock_request.return_value = mock_response

        stage = HttpFetcherStage(name="TestFetcher")
        input_data = {"url": "https://api.example.com/data"}

        result = stage.transform(input_data)

        assert result["status_code"] == 200
        assert result["data"] == {"result": "success"}
        assert result["content_type"] == "json"
        assert "elapsed" in result

    @patch('http_fetcher.http_client.HttpClient.request')
    def test_fetch_error_handling(self, mock_request):
        """Test error handling in fetch operations."""
        mock_request.side_effect = HttpError("Connection failed")

        stage = HttpFetcherStage(name="TestFetcher")
        input_data = {"url": "https://api.example.com/data"}

        result = stage.transform(input_data)

        assert result["error"] is True
        assert "Connection failed" in result["error_message"]
        assert result["original_request"] == input_data

    def test_fetcher_stats(self):
        """Test fetcher statistics reporting."""
        stage = HttpFetcherStage(name="TestFetcher")

        stats = stage.get_stats()
        assert stats["stage_name"] == "TestFetcher"
        assert stats["requests_made"] == 0
        assert stats["requests_successful"] == 0
        assert stats["requests_failed"] == 0


class TestBatchHttpFetcherStage:
    """Tests for batch HTTP fetcher stage."""

    def test_batch_fetcher_initialization(self):
        """Test batch fetcher initialization."""
        stage = BatchHttpFetcherStage(
            name="BatchFetcher",
            max_concurrent=5,
            requests_per_second=10.0
        )

        assert stage.name == "BatchFetcher"
        assert stage.max_concurrent == 5

    def test_batch_processing(self):
        """Test batch request processing."""
        stage = BatchHttpFetcherStage(name="BatchFetcher", max_concurrent=2)

        # Mock the underlying fetcher
        mock_fetcher = Mock()
        mock_fetcher.transform.side_effect = [
            {"status_code": 200, "data": "result1"},
            {"status_code": 200, "data": "result2"},
            {"status_code": 200, "data": "result3"}
        ]
        stage._fetcher_stage = mock_fetcher

        batch_data = [
            {"url": "https://api.example.com/1"},
            {"url": "https://api.example.com/2"},
            {"url": "https://api.example.com/3"}
        ]

        result = stage.transform(batch_data)

        assert len(result) == 3
        assert result[0]["data"] == "result1"
        assert result[1]["data"] == "result2"
        assert result[2]["data"] == "result3"

        # Verify calls were made
        assert mock_fetcher.transform.call_count == 3

    def test_batch_fetcher_stats(self):
        """Test batch fetcher statistics."""
        stage = BatchHttpFetcherStage(name="BatchFetcher", max_concurrent=3)

        stats = stage.get_stats()
        assert stats["stage_name"] == "BatchFetcher"
        assert stats["max_concurrent"] == 3


class TestIntegrationScenarios:
    """Tests for integration scenarios and edge cases."""

    def test_single_vs_batch_processing(self):
        """Test single request vs batch processing."""
        # Single request processing
        single_stage = HttpFetcherStage(name="SingleFetcher")

        # Mock successful response
        import time
        mock_response = HttpResponse(
            status_code=200,
            content=b'{"result": "ok"}',
            headers={"content-type": "application/json"},
            url="https://api.example.com/test",
            elapsed=0.1,
            request_time=time.time()
        )

        with patch.object(single_stage._http_client, 'request', return_value=mock_response):
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


if __name__ == "__main__":
    """Run advanced tests when executed directly."""
    pytest.main([__file__, "-v"])

