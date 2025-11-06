"""
Advanced async patterns and architectures.

This module covers:
- Producer-consumer patterns
- Data processing pipelines
- Fan-in/fan-out patterns
- Circuit breaker patterns
- Retry and backoff patterns
- Pub/sub patterns
- Request batching patterns
- Rate limiting patterns
"""

import asyncio
import random
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
from collections import deque


class AsyncPatternsExample:
    """
    Examples of advanced async patterns and architectures.
    """

    async def producer_consumer_queue(self) -> None:
        """Demonstrate producer-consumer pattern with asyncio.Queue."""
        print("=== Producer-Consumer with Queue ===")

        async def producer(producer_id: str, queue: asyncio.Queue) -> None:
            """Producer that generates items."""
            for i in range(5):
                item = f"Item-{producer_id}-{i+1}"
                await queue.put(item)
                print(f"📦 Producer {producer_id}: produced {item}")
                await asyncio.sleep(random.uniform(0.1, 0.3))

            # Signal completion
            await queue.put(None)
            print(f"📦 Producer {producer_id}: finished producing")

        async def consumer(consumer_id: str, queue: asyncio.Queue) -> None:
            """Consumer that processes items."""
            items_processed = 0
            while True:
                item = await queue.get()

                if item is None:
                    # Put the sentinel back for other consumers
                    await queue.put(None)
                    break

                # Process item
                await asyncio.sleep(random.uniform(0.2, 0.5))
                items_processed += 1
                print(f"🍽️  Consumer {consumer_id}: processed {item}")

            print(f"🍽️  Consumer {consumer_id}: processed {items_processed} items")

        # Create shared queue
        queue = asyncio.Queue(maxsize=3)  # Bounded queue

        # Start producers and consumers
        producers = [asyncio.create_task(producer(f"P{i+1}", queue)) for i in range(2)]
        consumers = [asyncio.create_task(consumer(f"C{i+1}", queue)) for i in range(2)]

        # Wait for producers to complete
        await asyncio.gather(*producers)

        # Wait for consumers to finish processing
        await asyncio.gather(*consumers)

        print("Producer-consumer pattern completed!\n")

    async def data_pipeline_pattern(self) -> None:
        """Demonstrate data processing pipeline pattern."""
        print("=== Data Processing Pipeline ===")

        async def data_source() -> AsyncGenerator[Dict[str, Any], None]:
            """Generate raw data."""
            data_items = [
                {"id": 1, "raw_value": 10, "category": "A"},
                {"id": 2, "raw_value": 25, "category": "B"},
                {"id": 3, "raw_value": 15, "category": "A"},
                {"id": 4, "raw_value": 30, "category": "C"},
                {"id": 5, "raw_value": 20, "category": "B"},
            ]

            for item in data_items:
                await asyncio.sleep(0.1)  # Simulate data arrival
                yield item

        async def stage1_filter(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """Stage 1: Filter and validate data."""
            await asyncio.sleep(0.05)  # Processing time

            if item["raw_value"] >= 15:  # Filter condition
                item["stage1"] = "filtered"
                item["filtered_at"] = time.time()
                return item

            return None  # Filtered out

        async def stage2_transform(item: Dict[str, Any]) -> Dict[str, Any]:
            """Stage 2: Transform data."""
            await asyncio.sleep(0.08)  # Processing time

            # Transform value
            item["transformed_value"] = item["raw_value"] * 1.5
            item["stage2"] = "transformed"
            item["transformed_at"] = time.time()
            return item

        async def stage3_aggregate(queue: asyncio.Queue) -> Dict[str, Any]:
            """Stage 3: Aggregate results."""
            results = []
            category_totals = {}

            while True:
                item = await queue.get()
                if item is None:
                    break

                results.append(item)

                # Aggregate by category
                cat = item["category"]
                if cat not in category_totals:
                    category_totals[cat] = {"count": 0, "total_value": 0}
                category_totals[cat]["count"] += 1
                category_totals[cat]["total_value"] += item["transformed_value"]

            # Calculate averages
            for cat, stats in category_totals.items():
                stats["avg_value"] = stats["total_value"] / stats["count"]

            return {
                "total_processed": len(results),
                "results": results,
                "category_stats": category_totals
            }

        # Set up pipeline queues
        stage1_to_2 = asyncio.Queue()
        stage2_to_3 = asyncio.Queue()

        # Stage 1: Source -> Filter
        async def pipeline_stage1():
            async for item in data_source():
                print(f"📥 Source: received {item}")

                filtered = await stage1_filter(item)
                if filtered:
                    await stage1_to_2.put(filtered)
                    print(f"🔍 Filter: passed {filtered['id']}")
                else:
                    print(f"🔍 Filter: rejected {item['id']}")

        # Stage 2: Filter -> Transform
        async def pipeline_stage2():
            while True:
                item = await stage1_to_2.get()
                if item is None:
                    await stage2_to_3.put(None)
                    break

                transformed = await stage2_transform(item)
                await stage2_to_3.put(transformed)
                print(f"⚙️  Transform: processed {transformed['id']}")

        # Start pipeline stages
        stage1_task = asyncio.create_task(pipeline_stage1())
        stage2_task = asyncio.create_task(pipeline_stage2())
        stage3_task = asyncio.create_task(stage3_aggregate(stage2_to_3))

        # Wait for stage 1 to complete
        await stage1_task

        # Signal stage 2 completion
        await stage1_to_2.put(None)

        # Wait for stage 2 to complete
        await stage2_task

        # Get final results
        final_results = await stage3_task

        # Display results
        print("\n📊 Pipeline Results:")
        print(f"  Total processed: {final_results['total_processed']}")

        print("  Category statistics:")
        for cat, stats in final_results['category_stats'].items():
            print(f"    {cat}: count={stats['count']}, avg={stats['avg_value']:.1f}")

        print()

    async def pub_sub_pattern(self) -> None:
        """Demonstrate publish-subscribe pattern."""
        print("=== Publish-Subscribe Pattern ===")

        class AsyncPubSub:
            """Simple async pub-sub implementation."""
            def __init__(self):
                self.subscribers: Dict[str, List[asyncio.Queue]] = {}
                self.lock = asyncio.Lock()

            async def subscribe(self, topic: str) -> asyncio.Queue:
                """Subscribe to a topic."""
                async with self.lock:
                    if topic not in self.subscribers:
                        self.subscribers[topic] = []

                    queue = asyncio.Queue()
                    self.subscribers[topic].append(queue)
                    print(f"📡 Subscribed to topic: {topic}")
                    return queue

            async def publish(self, topic: str, message: Any) -> None:
                """Publish message to topic."""
                async with self.lock:
                    if topic in self.subscribers:
                        # Publish to all subscribers
                        publish_tasks = [
                            subscriber.put(message)
                            for subscriber in self.subscribers[topic]
                        ]
                        await asyncio.gather(*publish_tasks)
                        print(f"📢 Published to {len(self.subscribers[topic])} subscribers: {topic}")

            async def unsubscribe(self, topic: str, queue: asyncio.Queue) -> None:
                """Unsubscribe from topic."""
                async with self.lock:
                    if topic in self.subscribers and queue in self.subscribers[topic]:
                        self.subscribers[topic].remove(queue)
                        print(f"📴 Unsubscribed from topic: {topic}")

        async def publisher(pubsub: AsyncPubSub, topic: str) -> None:
            """Publisher task."""
            messages = ["Message 1", "Message 2", "Message 3", "END"]

            for message in messages:
                await pubsub.publish(topic, message)
                await asyncio.sleep(0.3)

        async def subscriber(sub_id: str, pubsub: AsyncPubSub, topic: str) -> None:
            """Subscriber task."""
            queue = await pubsub.subscribe(topic)

            try:
                while True:
                    message = await queue.get()
                    if message == "END":
                        break

                    print(f"📨 Subscriber {sub_id}: received '{message}'")
                    await asyncio.sleep(0.1)  # Simulate processing

            finally:
                await pubsub.unsubscribe(topic, queue)

        # Create pub-sub system
        pubsub = AsyncPubSub()

        # Start publisher and subscribers
        publisher_task = asyncio.create_task(publisher(pubsub, "news"))
        subscriber_tasks = [
            asyncio.create_task(subscriber(f"S{i+1}", pubsub, "news"))
            for i in range(3)
        ]

        # Wait for completion
        await asyncio.gather(publisher_task, *subscriber_tasks)

        print("Pub-sub pattern completed!\n")

    async def circuit_breaker_pattern(self) -> None:
        """Demonstrate circuit breaker pattern for fault tolerance."""
        print("=== Circuit Breaker Pattern ===")

        class AsyncCircuitBreaker:
            """Async circuit breaker implementation."""
            def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 2.0):
                self.failure_threshold = failure_threshold
                self.recovery_timeout = recovery_timeout
                self.failure_count = 0
                self.last_failure_time: Optional[float] = None
                self.state = "closed"  # closed, open, half-open
                self.lock = asyncio.Lock()

            async def call(self, coro_func, *args, **kwargs):
                """Execute coroutine with circuit breaker protection."""
                async with self.lock:
                    if self.state == "open":
                        if self._should_attempt_reset():
                            self.state = "half-open"
                            print("🔄 Circuit breaker: attempting reset")
                        else:
                            raise Exception("Circuit breaker is OPEN")

                try:
                    result = await coro_func(*args, **kwargs)
                    await self._on_success()
                    return result
                except Exception as e:
                    await self._on_failure()
                    raise e

            async def _on_success(self):
                """Handle successful call."""
                async with self.lock:
                    if self.state == "half-open":
                        self.state = "closed"
                        self.failure_count = 0
                        print("✅ Circuit breaker: reset successful")
                    elif self.state == "closed":
                        self.failure_count = 0

            async def _on_failure(self):
                """Handle failed call."""
                async with self.lock:
                    self.failure_count += 1
                    self.last_failure_time = time.time()

                    if self.failure_count >= self.failure_threshold:
                        self.state = "open"
                        print(f"🚫 Circuit breaker: opened after {self.failure_count} failures")

            def _should_attempt_reset(self) -> bool:
                """Check if we should attempt to reset the circuit."""
                if self.last_failure_time is None:
                    return True
                return time.time() - self.last_failure_time >= self.recovery_timeout

        async def unreliable_service(call_id: str) -> str:
            """Unreliable service that may fail."""
            if random.random() > 0.7:  # 30% failure rate
                await asyncio.sleep(0.1)
                raise ConnectionError(f"Service unavailable for {call_id}")

            await asyncio.sleep(0.2)
            return f"Success: {call_id}"

        # Create circuit breaker
        breaker = AsyncCircuitBreaker(failure_threshold=2, recovery_timeout=1.5)

        # Test calls
        call_ids = [f"call_{i+1}" for i in range(10)]

        print("Testing circuit breaker with unreliable service:")
        for call_id in call_ids:
            try:
                result = await breaker.call(unreliable_service, call_id)
                print(f"  ✅ {call_id}: {result}")
            except Exception as e:
                print(f"  ❌ {call_id}: {e}")

            await asyncio.sleep(0.2)

        print()

    async def retry_with_backoff_pattern(self) -> None:
        """Demonstrate retry with exponential backoff pattern."""
        print("=== Retry with Backoff Pattern ===")

        async def unreliable_operation(attempt: int) -> str:
            """Operation that fails initially but succeeds later."""
            # Fail first 2 attempts, succeed on 3rd
            if attempt < 3:
                raise ConnectionError(f"Attempt {attempt} failed")

            return f"Success on attempt {attempt}"

        async def retry_with_backoff(coro_func, max_attempts: int = 5,
                                   base_delay: float = 0.1, max_delay: float = 5.0):
            """Retry function with exponential backoff."""
            for attempt in range(max_attempts):
                try:
                    return await coro_func(attempt + 1)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e  # Last attempt failed

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    # Add jitter to prevent thundering herd
                    jitter = random.uniform(0.1, 1.0) * delay * 0.1
                    total_delay = delay + jitter

                    print(f"  Attempt {attempt + 1} failed: {e}")
                    print(".2f")
                    await asyncio.sleep(total_delay)

            raise RuntimeError("Should not reach here")

        # Test retry mechanism
        print("Testing retry with exponential backoff:")
        try:
            result = await retry_with_backoff(unreliable_operation, max_attempts=5)
            print(f"  🎉 Final result: {result}")
        except Exception as e:
            print(f"  💥 All retries failed: {e}")

        print()

    async def rate_limiting_pattern(self) -> None:
        """Demonstrate rate limiting pattern."""
        print("=== Rate Limiting Pattern ===")

        class AsyncRateLimiter:
            """Token bucket rate limiter."""
            def __init__(self, rate: float, capacity: int):
                self.rate = rate  # tokens per second
                self.capacity = capacity
                self.tokens = capacity
                self.last_update = time.time()
                self.lock = asyncio.Lock()

            async def acquire(self, tokens: int = 1) -> bool:
                """Acquire tokens from the bucket."""
                async with self.lock:
                    now = time.time()
                    # Add tokens based on time passed
                    elapsed = now - self.last_update
                    self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                    self.last_update = now

                    # Check if we have enough tokens
                    if self.tokens >= tokens:
                        self.tokens -= tokens
                        return True

                    return False

            async def wait_for_tokens(self, tokens: int = 1) -> None:
                """Wait until tokens are available."""
                while not await self.acquire(tokens):
                    # Wait a bit before retrying
                    await asyncio.sleep(0.1)

        async def rate_limited_task(task_id: str, limiter: AsyncRateLimiter) -> None:
            """Task that respects rate limits."""
            await limiter.wait_for_tokens()
            print(f"🚀 Task {task_id}: executing")
            await asyncio.sleep(0.1)  # Simulate work
            print(f"✅ Task {task_id}: completed")

        # Create rate limiter (10 requests per second, capacity 5)
        limiter = AsyncRateLimiter(rate=10, capacity=5)

        print("Testing rate limiting (10 req/sec):")
        start_time = time.time()

        # Launch many tasks simultaneously
        tasks = [rate_limited_task(f"T{i+1}", limiter) for i in range(15)]
        await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        print(".2f")
        print(".1f")
        print()

    async def request_batching_pattern(self) -> None:
        """Demonstrate request batching pattern for efficiency."""
        print("=== Request Batching Pattern ===")

        async def process_batch(batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """Process a batch of requests efficiently."""
            print(f"🔄 Processing batch of {len(batch)} requests...")

            # Simulate batch processing overhead (fixed cost)
            await asyncio.sleep(0.2)  # Batch setup time

            results = []
            for request in batch:
                # Simulate individual processing time
                await asyncio.sleep(0.05)
                result = {
                    "request_id": request["id"],
                    "result": f"processed_{request['data']}",
                    "batch_size": len(batch)
                }
                results.append(result)

            print(f"✅ Batch processed: {len(results)} results")
            return results

        class RequestBatcher:
            """Batch requests for efficient processing."""
            def __init__(self, batch_size: int = 5, timeout: float = 1.0):
                self.batch_size = batch_size
                self.timeout = timeout
                self.pending_requests: deque = deque()
                self.lock = asyncio.Lock()
                self.event = asyncio.Event()

            async def submit_request(self, request: Dict[str, Any]) -> Any:
                """Submit a request for batching."""
                async with self.lock:
                    self.pending_requests.append(request)
                    request_count = len(self.pending_requests)

                    # If we have enough requests, trigger processing
                    if request_count >= self.batch_size:
                        self.event.set()
                    else:
                        self.event.clear()

                # Wait for batch processing or timeout
                try:
                    await asyncio.wait_for(self.event.wait(), timeout=self.timeout)
                except asyncio.TimeoutError:
                    # Timeout - process current batch anyway
                    pass

                # Wait for our result
                return await self._wait_for_result(request)

            async def _wait_for_result(self, request: Dict[str, Any]) -> Any:
                """Wait for the result of a specific request."""
                # In a real implementation, you'd track individual requests
                # For demo, just return a mock result
                await asyncio.sleep(0.01)
                return f"result_for_{request['id']}"

            async def process_batches(self) -> None:
                """Process batches as they become available."""
                while True:
                    async with self.lock:
                        if len(self.pending_requests) >= self.batch_size:
                            batch = []
                            for _ in range(self.batch_size):
                                batch.append(self.pending_requests.popleft())
                        else:
                            await asyncio.sleep(0.1)
                            continue

                    # Process the batch
                    results = await process_batch(batch)

                    # Signal completion
                    self.event.set()

        # Create batcher
        batcher = asyncio.create_task(RequestBatcher(batch_size=3, timeout=2.0).process_batches())

        # Submit requests
        requests = [{"id": f"req_{i+1}", "data": f"data_{i+1}"} for i in range(8)]

        print("Submitting requests for batching:")
        submit_tasks = [batcher.submit_request(req) for req in requests]

        results = await asyncio.gather(*submit_tasks)

        print("All requests completed:")
        for i, result in enumerate(results):
            print(f"  {requests[i]['id']}: {result}")

        # Stop batcher
        batcher.cancel()
        try:
            await batcher
        except asyncio.CancelledError:
            pass

        print()

    async def fan_out_fan_in_pattern(self) -> None:
        """Demonstrate fan-out/fan-in pattern."""
        print("=== Fan-Out/Fan-In Pattern ===")

        async def worker(task_id: str, data: Any) -> Dict[str, Any]:
            """Worker that processes data."""
            # Simulate variable processing time
            await asyncio.sleep(random.uniform(0.1, 0.4))

            result = {
                "task_id": task_id,
                "input": data,
                "output": f"processed_{data}",
                "worker": f"worker_{random.randint(1, 3)}"
            }
            return result

        # Generate work items
        work_items = [f"item_{i+1}" for i in range(12)]
        print(f"Work items: {work_items}")

        # Fan-out: Distribute work to workers
        print("📤 Fan-out: Distributing work...")
        worker_tasks = [
            worker(f"task_{i+1}", item)
            for i, item in enumerate(work_items)
        ]

        # Fan-in: Collect results as they complete
        print("📥 Fan-in: Collecting results...")
        results = []
        for coro in asyncio.as_completed(worker_tasks):
            result = await coro
            results.append(result)
            print(f"  ✓ Completed: {result['task_id']} -> {result['output']}")

        print(f"\nFan-out/fan-in completed: {len(results)} results processed")
        print()


async def main() -> None:
    """Run all async patterns examples."""
    print("Asyncio Patterns Examples")
    print("=" * 25)

    example = AsyncPatternsExample()

    await example.producer_consumer_queue()
    await example.data_pipeline_pattern()
    await example.pub_sub_pattern()
    await example.circuit_breaker_pattern()
    await example.retry_with_backoff_pattern()
    await example.rate_limiting_pattern()
    await example.request_batching_pattern()
    await example.fan_out_fan_in_pattern()

    print("All async patterns examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
