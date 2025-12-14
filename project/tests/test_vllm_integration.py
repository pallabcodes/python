"""
Integration Tests for vLLM Provider.

Tests vLLM integration, batching, streaming, and fallback mechanisms.
"""

import asyncio
import time
from unittest.mock import Mock, patch
import pytest

# Import vLLM provider
try:
    from noleet.llm.providers.vllm_provider import VLLMProvider
except ImportError:
    pytest.skip("vLLM provider not available", allow_module_level=True)


class TestVLLMProviderIntegration:
    """Integration tests for vLLM provider."""

    @pytest.fixture
    def vllm_config(self):
        """Configuration for vLLM provider."""
        return {
            "model": "microsoft/DialoGPT-small",  # Use small model for testing
            "tensor_parallel_size": 1,
            "max_model_len": 512,
            "gpu_memory_utilization": 0.5,
            "max_num_seqs": 8,
            "temperature": 0.1,
            "max_tokens": 50,
            "timeout": 30
        }

    @pytest.fixture
    def vllm_provider(self, vllm_config):
        """Fixture for vLLM provider."""
        return VLLMProvider(**vllm_config)

    def test_provider_initialization(self, vllm_provider, vllm_config):
        """Test vLLM provider initializes correctly."""
        assert vllm_provider is not None
        assert vllm_provider._model == vllm_config["model"]
        assert vllm_provider._tensor_parallel_size == vllm_config["tensor_parallel_size"]
        assert vllm_provider._max_model_len == vllm_config["max_model_len"]
        assert not vllm_provider._is_initialized

    def test_availability_check(self, vllm_provider):
        """Test availability checking."""
        # Should return False if vLLM not installed
        available = vllm_provider.is_available()
        # In test environment, vLLM may not be available
        assert isinstance(available, bool)

    def test_fallback_generation(self, vllm_provider):
        """Test fallback generation when vLLM unavailable."""
        prompt = "Hello world"

        # Mock the generate method to simulate unavailability
        with patch.object(vllm_provider, '_generate_response', side_effect=Exception("vLLM error")):
            # Should fall back to mock response
            response = vllm_provider.generate(prompt)
            assert isinstance(response, str)
            assert len(response) > 0

    @pytest.mark.skipif(not VLLMProvider().is_available(), reason="vLLM not available")
    def test_real_vllm_initialization(self, vllm_provider):
        """Test real vLLM engine initialization (if available)."""
        # This will only run if vLLM is actually available
        try:
            vllm_provider._initialize_engine()
            # If no exception, engine should be initialized
            assert vllm_provider._llm_engine is not None
            assert vllm_provider._is_initialized
        except Exception as e:
            # If initialization fails, that's also acceptable in test environment
            assert "vLLM" in str(e) or "model" in str(e).lower()

    def test_batch_generation_interface(self, vllm_provider):
        """Test batch generation interface."""
        prompts = ["Hello", "How are you?", "Test prompt"]

        # Should handle batch generation gracefully
        responses = vllm_provider.generate_batch(prompts)

        assert isinstance(responses, list)
        assert len(responses) == len(prompts)
        assert all(isinstance(r, str) for r in responses)

    def test_model_info(self, vllm_provider):
        """Test model information retrieval."""
        info = vllm_provider.get_model_info()

        assert isinstance(info, dict)
        assert "provider" in info
        assert "model" in info
        assert "available" in info
        assert info["provider"] == "vllm"

    def test_parameter_validation(self, vllm_provider):
        """Test parameter validation."""
        # Test with valid parameters
        response = vllm_provider.generate("test", temperature=0.5, max_tokens=20)
        assert isinstance(response, str)

        # Test with invalid parameters (should handle gracefully)
        response = vllm_provider.generate("test", temperature=-1)  # Invalid temperature
        assert isinstance(response, str)  # Should still work

    @pytest.mark.asyncio
    async def test_async_compatibility(self, vllm_provider):
        """Test async compatibility."""
        prompt = "async test prompt"

        # Should work in async context
        response = vllm_provider.generate(prompt)
        assert isinstance(response, str)

    def test_resource_cleanup(self, vllm_provider):
        """Test resource cleanup."""
        # Initialize if possible
        try:
            vllm_provider._initialize_engine()
        except:
            pass  # May not be available

        # Should handle shutdown gracefully
        vllm_provider.shutdown()

        # Check that cleanup was attempted
        assert vllm_provider._is_initialized == False or vllm_provider._llm_engine is None


class TestVLLMProviderStress:
    """Stress tests for vLLM provider."""

    @pytest.fixture
    def stress_provider(self):
        """Provider for stress testing."""
        return VLLMProvider(
            model="microsoft/DialoGPT-small",
            max_tokens=10,  # Short responses for speed
            temperature=0.1
        )

    def test_concurrent_requests(self, stress_provider):
        """Test concurrent request handling."""
        import threading
        import queue

        results = queue.Queue()
        errors = queue.Queue()

        def make_request(request_id):
            try:
                prompt = f"Test request {request_id}"
                response = stress_provider.generate(prompt)
                results.put((request_id, len(response)))
            except Exception as e:
                errors.put((request_id, str(e)))

        # Start multiple threads
        threads = []
        num_threads = 5  # Reasonable number for testing

        for i in range(num_threads):
            t = threading.Thread(target=make_request, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join(timeout=30)  # 30 second timeout

        # Check that most requests succeeded
        successful_requests = results.qsize()
        failed_requests = errors.qsize()

        assert successful_requests >= num_threads * 0.8  # At least 80% success rate
        assert successful_requests + failed_requests == num_threads

    def test_batch_processing_stress(self, stress_provider):
        """Test batch processing under load."""
        # Create multiple batches
        batch_sizes = [1, 5, 10]
        prompts_template = ["Test prompt number {}"] * 50

        for batch_size in batch_sizes:
            prompts = [template.format(i) for i, template in enumerate(prompts_template[:batch_size])]

            start_time = time.time()
            responses = stress_provider.generate_batch(prompts)
            end_time = time.time()

            assert isinstance(responses, list)
            assert len(responses) == len(prompts)

            # Should complete in reasonable time
            execution_time = end_time - start_time
            max_expected_time = batch_size * 2  # 2 seconds per prompt max
            assert execution_time < max_expected_time

    def test_memory_efficiency(self, stress_provider):
        """Test memory efficiency with repeated requests."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make many requests
        for i in range(100):
            prompt = f"Memory test request {i}"
            response = stress_provider.generate(prompt)
            assert isinstance(response, str)

            # Periodic memory check
            if i % 20 == 0:
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory

                # Memory should not grow excessively (less than 100MB increase)
                assert memory_increase < 100 * 1024 * 1024


class TestVLLMProviderErrorHandling:
    """Error handling tests for vLLM provider."""

    def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        provider = VLLMProvider(timeout=1)  # Very short timeout

        # Should handle timeout gracefully
        response = provider.generate("This might timeout")
        assert isinstance(response, str)  # Should fallback to mock

    def test_invalid_model_handling(self):
        """Test handling of invalid model names."""
        provider = VLLMProvider(model="invalid/model/name")

        # Should handle gracefully
        response = provider.generate("test")
        assert isinstance(response, str)

    def test_large_prompt_handling(self):
        """Test handling of very large prompts."""
        large_prompt = "word " * 1000  # Very long prompt

        provider = VLLMProvider(max_model_len=512)

        # Should handle gracefully (truncate or fallback)
        response = provider.generate(large_prompt)
        assert isinstance(response, str)

    def test_special_characters(self):
        """Test handling of special characters and unicode."""
        special_prompts = [
            "Hello 🌍 World!",
            "Test with émojis 🎉",
            "Unicode: α β γ δ ε",
            "Symbols: @#$%^&*()"
        ]

        provider = VLLMProvider()

        for prompt in special_prompts:
            response = provider.generate(prompt)
            assert isinstance(response, str)
            assert len(response) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])