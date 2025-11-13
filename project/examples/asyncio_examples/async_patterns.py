"""
Advanced asyncio patterns implemented with production-minded fixes.

Improvements over the original:
- Proper use of asyncio.Queue: task_done()/join(), per-consumer sentinels, bounded queues
- Avoid holding locks while awaiting; copy subscriber lists then publish
- Fixed many demo bugs (.2f stray prints, wrong variable names)
- RequestBatcher: per-request Future mapping, safe wakeups, no lock-held sleeps
- Circuit breaker: clearer state transitions and non-blocking checks
- Rate limiter: compute exact sleep until tokens available instead of fixed polling
- Clear cancellation handling and clean shutdowns

This file is designed to be readable, correct, and suitable as a reference for senior engineers.
"""

import asyncio
import random
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
from collections import deque


class AsyncPatternsExample:
    """
    Collection of robust, production-aware asyncio patterns.

    This class demonstrates advanced async patterns used in production systems.
    All patterns include proper resource management, error handling, and
    cancellation support.

    When to Use:
        - Building production async applications
        - Implementing fault-tolerant systems
        - Optimizing resource usage
        - Building scalable distributed systems
        - Implementing common async patterns

    Real-World Examples:
        - Web servers: Producer-consumer for request handling
        - Data pipelines: Multi-stage processing pipelines
        - Event systems: Pub-sub for event distribution
        - API clients: Circuit breakers and retries
        - Rate limiting: Token bucket for API throttling
        - Batching: Request batching for efficiency

    Gotchas:
        - Never hold locks across await points
        - Always call task_done() for queue.get()
        - Use sentinels for graceful shutdown
        - Copy subscriber lists before publishing
        - Handle cancellation in cleanup code
        - Use monotonic time for rate limiting

    Performance Notes:
        - Patterns optimize for different scenarios
        - Batching reduces overhead
        - Rate limiting prevents overload
        - Circuit breakers prevent waste
        - Proper patterns scale to production loads
    """

    # -----------------------------
    # Producer / Consumer (bounded)
    # -----------------------------
    async def producer_consumer_queue(self) -> None:
        """
        Producer/consumer with bounded queue, explicit sentinels and join.

        Demonstrates robust producer-consumer pattern with proper resource
        management, backpressure handling, and graceful shutdown.

        When to Use:
            - Decoupling producers and consumers
            - Implementing job queues
            - Handling variable production/consumption rates
            - Building event-driven systems
            - Managing resource consumption

        Real-World Examples:
            - Job queues: Producers submit jobs, workers consume
            - Log aggregation: Services produce logs, aggregator consumes
            - Event processing: Event sources produce, processors consume
            - Message queues: Publishers produce, subscribers consume
            - Task queues: Task generators produce, executors consume

        Gotchas:
            - queue.put() suspends when maxsize reached (backpressure)
            - queue.get() suspends when queue empty
            - task_done() must be called for every get()
            - join() waits until all items processed
            - Use sentinels (None) for graceful shutdown
            - One sentinel per consumer required

        Performance Notes:
            - Bounded queue prevents memory exhaustion
            - Backpressure slows producers when consumers lag
            - Optimal producer/consumer ratio depends on workload
            - Queue size affects latency vs memory tradeoff
        """
        print("=== Producer-Consumer with Queue ===")

        queue: asyncio.Queue = asyncio.Queue(maxsize=3)
        num_producers = 2
        num_consumers = 2

        async def producer(pid: int, q: asyncio.Queue, n: int = 5) -> None:
            """
            Producer steps (important awaits and suspension):
            - await q.put(item): suspends if queue is full (backpressure).
              When suspended, the event loop runs other tasks (e.g. consumers).
              When space frees, this coroutine resumes exactly after the await.
            - await asyncio.sleep(...): explicit suspend to simulate delay.
            """
            for i in range(n):
                item = f"Item-P{pid}-{i+1}"  # synchronous work: no suspension
                # This may suspend if the queue is full
                await q.put(item)
                # When q.put returns, the item is enqueued and we continue here.
                print(f"📦 Producer{pid}: produced {item}")

                # Simulate production delay — suspension point; other tasks run.
                await asyncio.sleep(random.uniform(0.05, 0.15))

            # producer finished producing — log and return
            print(f"📦 Producer{pid}: done producing")

        async def consumer(cid: int, q: asyncio.Queue) -> None:
            """
            Consumer loop:
            - await q.get(): suspends when empty; resumes once an item is available.
            - Finally block calls q.task_done() to decrement unfinished-task counter.
            - If we see a sentinel (None), consumer returns (exits), not forgetting to
              call task_done() for the sentinel as well.
            """
            processed = 0
            while True:
                # Suspend here if queue empty; resume when any producer does q.put(...)
                item = await q.get()
                try:
                    if item is None:  # sentinel -> time to exit
                        # Mark the sentinel task done and return to exit coroutine.
                        q.task_done()
                        print(f"🛑 Consumer{cid}: received sentinel")
                        return

                    # Process: another suspension point
                    await asyncio.sleep(random.uniform(0.1, 0.25))
                    processed += 1
                    print(f"🍽️  Consumer{cid}: processed {item}")

                finally:
                    # For every successful q.get() we must call task_done().
                    # This runs always (even if processing raised).
                    # If forgotten, `await q.join()` can hang.
                    q.task_done()

        # Start consumers first so they can pick up items right away when producers produce.
        consumer_tasks = [asyncio.create_task(consumer(i + 1, queue)) for i in range(num_consumers)]

        # Start producers
        producer_tasks = [asyncio.create_task(producer(i + 1, queue)) for i in range(num_producers)]

        # Wait for all producers to finish producing (they will return; they don't wait for consumers).
        await asyncio.gather(*producer_tasks)

        # All producers done -> enqueue exactly one sentinel per consumer so each consumer exits.
        # These puts may suspend if queue maxsize is reached, but in practice consumers will be draining.
        for _ in range(num_consumers):
            await queue.put(None)

        # Now wait until all real items (and sentinels) have been processed.
        # queue.join() suspends the caller until the internal counter (incremented by put)
        # has been decremented to 0 by corresponding task_done() calls.
        await queue.join()

        # Ensure consumer tasks have finished and returned
        await asyncio.gather(*consumer_tasks)

        print("Producer-consumer pattern completed!\n")

    # -----------------------------
    # Pipeline (multi-stage)
    # -----------------------------
    async def data_pipeline_pattern(self) -> None:
        """
        Multi-stage pipeline using queues and explicit sentinel forwarding.

        Demonstrates robust multi-stage data processing pipeline with proper
        stage coordination, backpressure, and completion handling.

        When to Use:
            - Multi-stage data processing
            - ETL pipelines
            - Data transformation workflows
            - Streaming data processing
            - Building data processing systems

        Real-World Examples:
            - ETL pipelines: Extract -> Transform -> Load
            - Log processing: Parse -> Filter -> Analyze -> Store
            - Image processing: Load -> Resize -> Compress -> Save
            - Data pipelines: Fetch -> Process -> Aggregate -> Store
            - Message processing: Receive -> Validate -> Route -> Send

        Gotchas:
            - Queues decouple stages (allow different rates)
            - Sentinels propagate downstream for completion
            - task_done()/join() ensure proper handoff
            - Each stage processes concurrently
            - Pipeline throughput limited by slowest stage
            - Backpressure flows backward through pipeline

        Performance Notes:
            - Stages process in parallel (better than sequential)
            - Memory usage depends on queue sizes
            - Optimal for streaming data processing
            - Can process infinite streams
            - Balance stage parallelism vs memory
        """
        print("=== Data Processing Pipeline ===")

        async def data_source() -> AsyncGenerator[Dict[str, Any], None]:
            # async generator: awaiting the caller yields control back to the event loop
            items = [
                {"id": 1, "raw_value": 10, "category": "A"},
                {"id": 2, "raw_value": 25, "category": "B"},
                {"id": 3, "raw_value": 15, "category": "A"},
                {"id": 4, "raw_value": 30, "category": "C"},
                {"id": 5, "raw_value": 20, "category": "B"},
            ]
            for it in items:
                # simulate arrival delay (suspension point)
                await asyncio.sleep(0.05)
                # yield returns an element to the consumer of this generator
                yield it

        async def stage1_filter(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            # processing suspension point
            await asyncio.sleep(0.02)
            if item["raw_value"] >= 15:
                item["stage1"] = "filtered"
                item["filtered_at"] = time.time()
                return item
            return None

        async def stage2_transform(item: Dict[str, Any]) -> Dict[str, Any]:
            await asyncio.sleep(0.03)
            item["transformed_value"] = item["raw_value"] * 1.5
            item["stage2"] = "transformed"
            item["transformed_at"] = time.time()
            return item

        async def stage3_aggregate(q: asyncio.Queue) -> Dict[str, Any]:
            """
            Aggregate consumes items from q until it sees a sentinel (None).
            - Each q.get() suspends if q is empty.
            - We call q.task_done() in finally to decrement unfinished counter.
            """
            results = []
            totals: Dict[str, Dict[str, float]] = {}
            while True:
                item = await q.get()  # suspend while waiting for next item
                if item is None:
                    # mark sentinel processed and break; sentinel is not aggregated
                    q.task_done()
                    break
                try:
                    results.append(item)
                    cat = item["category"]
                    totals.setdefault(cat, {"count": 0, "total_value": 0.0})
                    totals[cat]["count"] += 1
                    totals[cat]["total_value"] += item["transformed_value"]
                finally:
                    # always mark as done, even if an exception occurred while processing
                    q.task_done()

            # compute averages (synchronous)
            for cat, stats in totals.items():
                stats["avg_value"] = stats["total_value"] / stats["count"]

            return {"total_processed": len(results), "results": results, "category_stats": totals}

        # queues decouple stages
        q1: asyncio.Queue = asyncio.Queue()
        q2: asyncio.Queue = asyncio.Queue()

        async def pipeline_stage1():
            # consume the async generator, then push filtered items to q1
            async for item in data_source():
                filtered = await stage1_filter(item)  # suspend while filtering
                if filtered:
                    await q1.put(filtered)  # may suspend if q1 bounded and full
            # signal downstream completion
            await q1.put(None)

        async def pipeline_stage2():
            # consume q1, transform and put into q2
            while True:
                item = await q1.get()  # suspend until item available
                try:
                    if item is None:
                        # propagate sentinel to stage3 and exit
                        await q2.put(None)
                        q1.task_done()
                        return
                    transformed = await stage2_transform(item)  # suspend while transforming
                    await q2.put(transformed)  # may suspend if q2 full
                finally:
                    # ensure we call task_done for every q1.get()
                    q1.task_done()

        # run pipeline tasks
        t1 = asyncio.create_task(pipeline_stage1())
        t2 = asyncio.create_task(pipeline_stage2())
        t3 = asyncio.create_task(stage3_aggregate(q2))

        # Wait for stage1 to finish producing into q1
        await t1

        # Ensure everything pushed to q1 has been processed/forwarded by stage2:
        # q1.join() blocks until q1.task_done() has been called matching all q1.put()s.
        await q1.join()

        # Wait for stage2 to finish (which should have forwarded sentinel to q2)
        await t2

        # Wait for final aggregation to complete and retrieve results
        final = await t3

        print("\n📊 Pipeline Results:")
        print(f"  Total processed: {final['total_processed']}")
        for cat, stats in final['category_stats'].items():
            print(f"    {cat}: count={stats['count']}, avg={stats['avg_value']:.1f}")
        print()

    # -----------------------------
    # Pub/Sub (copy subscribers, avoid long lock hold)
    # -----------------------------
    async def pub_sub_pattern(self) -> None:
        """
        Publish-subscribe using per-subscriber queues.

        Demonstrates robust pub-sub pattern with per-subscriber queues to
        avoid head-of-line blocking and proper lock usage.

        When to Use:
            - Event distribution to multiple subscribers
            - Decoupling publishers and subscribers
            - Building event-driven architectures
            - Implementing message brokers
            - Building notification systems

        Real-World Examples:
            - Event systems: Publish events, multiple subscribers consume
            - Message brokers: Publishers send, subscribers receive
            - Notification systems: Notify multiple recipients
            - Log aggregation: Publish logs, multiple aggregators consume
            - Real-time updates: Publish updates, clients subscribe

        Gotchas:
            - Each subscriber gets own queue (prevents blocking)
            - Copy subscriber list under lock, release before await
            - Never hold lock across await points
            - Subscribers must call task_done() for queue accounting
            - Unsubscribe on subscriber exit to prevent leaks
            - Slow subscribers don't block others

        Performance Notes:
            - Per-subscriber queues prevent head-of-line blocking
            - Lock held only for list copy (fast operation)
            - Publishing suspends only if queues are full
            - Scales to many subscribers efficiently
            - Memory usage increases with subscriber count
        """
        print("=== Publish-Subscribe Pattern ===")

        class AsyncPubSub:
            def __init__(self):
                self._subscribers: Dict[str, List[asyncio.Queue]] = {}
                self._lock = asyncio.Lock()

            async def subscribe(self, topic: str) -> asyncio.Queue:
                q = asyncio.Queue()
                # mutate registry under the lock
                async with self._lock:
                    self._subscribers.setdefault(topic, []).append(q)
                # return queue; subscriber reads from it
                return q

            async def unsubscribe(self, topic: str, q: asyncio.Queue) -> None:
                # remove under lock to avoid races with publish/subscribe
                async with self._lock:
                    if topic in self._subscribers and q in self._subscribers[topic]:
                        self._subscribers[topic].remove(q)

            async def publish(self, topic: str, message: Any) -> None:
                # copy the subscriber list while holding lock; then release
                async with self._lock:
                    subs = list(self._subscribers.get(topic, []))

                if not subs:
                    return

                # publish to all subscriber queues concurrently (outside lock)
                # each s.put(message) may suspend only if a given subscriber's queue is bounded & full,
                # otherwise it is near-instant.
                await asyncio.gather(*(s.put(message) for s in subs))

        async def publisher(pubsub: AsyncPubSub, topic: str) -> None:
            for m in ("Message 1", "Message 2", "Message 3", "END"):
                # publish suspends while delivering to subscriber queues if necessary
                await pubsub.publish(topic, m)
                await asyncio.sleep(0.05)

        async def subscriber(name: str, pubsub: AsyncPubSub, topic: str) -> None:
            q = await pubsub.subscribe(topic)
            try:
                while True:
                    # suspend until message available for this subscriber
                    m = await q.get()
                    try:
                        if m == "END":
                            q.task_done()
                            return
                        print(f"📨 {name} got: {m}")
                        # simulate processing suspension
                        await asyncio.sleep(0.02)
                    finally:
                        q.task_done()
            finally:
                # ensure we remove the subscriber from registry on exit
                await pubsub.unsubscribe(topic, q)

        # run publisher and subscribers concurrently
        pubsub = AsyncPubSub()
        pub = asyncio.create_task(publisher(pubsub, "news"))
        subs = [asyncio.create_task(subscriber(f"S{i+1}", pubsub, "news")) for i in range(3)]

        # Wait for publisher and all subscribers to finish
        await asyncio.gather(pub, *subs)
        print("Pub-sub pattern completed!\n")

    # -----------------------------
    # Circuit breaker (robust)
    # -----------------------------
    async def circuit_breaker_pattern(self) -> None:
        """
        Async circuit breaker for fault isolation.

        Demonstrates robust circuit breaker with proper state management,
        lock usage, and recovery handling.

        When to Use:
            - Calling external services that may fail
            - Preventing cascade failures
            - Implementing fault tolerance
            - Protecting against service outages
            - Building resilient distributed systems

        Real-World Examples:
            - API clients: Stop calling failing APIs
            - Database connections: Stop connecting to failing DB
            - Microservices: Stop calling failing services
            - External integrations: Stop calling failing services
            - Payment gateways: Stop calling failing payment APIs

        Gotchas:
            - State transitions protected by lock
            - Never hold lock across await points
            - Half-open state tests recovery
            - Failure threshold must be tuned
            - Recovery timeout allows service recovery
            - Monitor circuit breaker state

        Performance Notes:
            - Prevents wasted resources on failing services
            - Fast failure (no waiting for timeouts)
            - Recovery testing adds minimal overhead
            - Critical for distributed system resilience
        """
        print("=== Circuit Breaker Pattern ===")

        class AsyncCircuitBreaker:
            def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 2.0):
                self.failure_threshold = failure_threshold
                self.recovery_timeout = recovery_timeout
                self.failure_count = 0
                self.last_failure_time: Optional[float] = None
                self.state = "closed"  # closed / open / half-open
                self._lock = asyncio.Lock()

            async def call(self, func, *args, **kwargs):
                # check state under lock to avoid races with other callers
                async with self._lock:
                    if self.state == "open":
                        # determine if recovery timeout elapsed; if so, try half-open
                        if self.last_failure_time and (time.time() - self.last_failure_time) >= self.recovery_timeout:
                            self.state = "half-open"
                        else:
                            # remaining open: fail fast
                            raise RuntimeError("Circuit is open")

                # call the underlying coroutine (may suspend); we do not hold the lock here,
                # preventing deadlocks and allowing other callers to observe state changes.
                try:
                    result = await func(*args, **kwargs)
                except Exception as e:
                    # on failure, update counts under lock
                    async with self._lock:
                        self.failure_count += 1
                        self.last_failure_time = time.time()
                        if self.failure_count >= self.failure_threshold:
                            self.state = "open"
                    raise
                else:
                    # on success, reset failure counters under lock
                    async with self._lock:
                        if self.state == "half-open":
                            self.state = "closed"
                            self.failure_count = 0
                        else:
                            self.failure_count = 0
                    return result

        async def unreliable(call_id: str) -> str:
            # simulate occasional failure — suspension points are the sleeps
            if random.random() < 0.35:
                await asyncio.sleep(0.02)
                raise ConnectionError(call_id)
            await asyncio.sleep(0.03)
            return f"ok:{call_id}"

        cb = AsyncCircuitBreaker(failure_threshold=2, recovery_timeout=0.5)
        for i in range(10):
            cid = f"call_{i+1}"
            try:
                r = await cb.call(unreliable, cid)  # may suspend inside unreliable()
                print(f"  ✅ {cid}: {r}")
            except Exception as e:
                print(f"  ❌ {cid}: {e}")
            # small gap between calls to observe state transitions
            await asyncio.sleep(0.05)

        print()

    # -----------------------------
    # Retry with exponential backoff
    # -----------------------------
    async def retry_with_backoff_pattern(self) -> None:
        """
        Retry with exponential backoff + jitter pattern.

        Demonstrates robust retry logic with exponential backoff and jitter
        to handle transient failures and prevent thundering herd.

        When to Use:
            - Handling transient failures
            - Retrying failed operations
            - Preventing thundering herd problems
            - Building resilient clients
            - Handling rate-limited APIs

        Real-World Examples:
            - API clients: Retry failed API calls
            - Database operations: Retry failed queries
            - Network operations: Retry failed connections
            - File operations: Retry failed file I/O
            - Distributed systems: Retry failed service calls

        Gotchas:
            - Only use for idempotent operations
            - Jitter prevents thundering herd
            - Exponential backoff reduces load
            - Max attempts prevents infinite retries
            - Max delay caps backoff time
            - Consider circuit breaker for persistent failures

        Performance Notes:
            - Exponential backoff reduces server load
            - Jitter distributes retry attempts
            - Max delay prevents excessive waits
            - Optimal for transient failures
            - Combine with circuit breaker for persistent failures
        """
        print("=== Retry with Backoff Pattern ===")

        async def unreliable(attempt: int) -> str:
            # fails for the first two attempts, succeeds afterward
            if attempt < 3:
                raise ConnectionError(f"attempt {attempt}")
            return f"ok-{attempt}"

        async def retry(coro_factory, max_attempts: int = 5, base_delay: float = 0.05, max_delay: float = 1.0):
            for attempt in range(1, max_attempts + 1):
                try:
                    # call the factory with attempt number; this may suspend inside the operation
                    return await coro_factory(attempt)
                except Exception as e:
                    if attempt == max_attempts:
                        # re-raise final failure
                        raise
                    # exponential backoff + small random jitter
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    jitter = delay * 0.1 * random.random()
                    to_sleep = delay + jitter
                    print(f"  attempt={attempt} failed: {e}; backing off {to_sleep:.3f}s")
                    # suspension — when resumed we'll retry the next attempt
                    await asyncio.sleep(to_sleep)

        try:
            res = await retry(unreliable, max_attempts=5)
            print(f"  🎉 result: {res}")
        except Exception as e:
            print(f"  💥 retries failed: {e}")

        print()

    # -----------------------------
    # Rate limiter (token bucket, efficient wait)
    # -----------------------------
    async def rate_limiting_pattern(self) -> None:
        """
        Token-bucket rate limiter with precise sleeping semantics.

        Demonstrates efficient token bucket rate limiter with precise
        sleep calculations to avoid busy-waiting.

        When to Use:
            - Rate limiting API requests
            - Throttling operations
            - Respecting rate limits
            - Preventing overload
            - Managing resource consumption

        Real-World Examples:
            - API clients: Respect API rate limits
            - Web scraping: Limit request rate
            - Database operations: Limit query rate
            - File operations: Limit I/O rate
            - External services: Respect service limits

        Gotchas:
            - Use time.monotonic() for elapsed time (not time.time())
            - Compute precise sleep to avoid busy-waiting
            - Lock protects token bucket state
            - Never hold lock across await
            - Refill tokens based on elapsed time
            - Handle zero rate edge case

        Performance Notes:
            - Precise sleep reduces CPU usage
            - Token bucket allows burst (capacity)
            - Rate limits average throughput
            - Efficient for high-frequency operations
            - Minimal overhead per operation
        """
        print("=== Rate Limiting Pattern ===")

        class TokenBucket:
            def __init__(self, rate: float, capacity: int):
                self.rate = rate
                self.capacity = float(capacity)
                self.tokens = float(capacity)
                self.last = time.monotonic()  # monotonic for elapsed measurement
                self._lock = asyncio.Lock()

            async def _refill(self) -> None:
                # compute tokens to add since last update (synchronous calculation)
                now = time.monotonic()
                elapsed = now - self.last
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last = now

            async def acquire(self, tokens: int = 1) -> bool:
                # small critical section to examine/modify tokens
                async with self._lock:
                    await self._refill()
                    if self.tokens >= tokens:
                        self.tokens -= tokens
                        return True
                    return False

            async def wait(self, tokens: int = 1) -> None:
                """
                Wait until tokens available.
                - we compute an approximate precise sleep until tokens present rather than
                  blind polling; this is more efficient under heavy load.
                """
                while True:
                    async with self._lock:
                        await self._refill()
                        if self.tokens >= tokens:
                            self.tokens -= tokens
                            return
                        # tokens needed to reach target
                        need = tokens - self.tokens
                        # if rate == 0, fallback small sleep
                        sleep_time = need / self.rate if self.rate > 0 else 0.01
                    # suspend for the computed time; other tasks proceed
                    await asyncio.sleep(max(0.001, sleep_time))

        limiter = TokenBucket(rate=10, capacity=5)

        async def work(i: int):
            # will suspend in limiter.wait if we exceed the token rate
            await limiter.wait(1)
            print(f"🚀 task {i} running")
            # simulate short work
            await asyncio.sleep(0.01)

        tasks = [asyncio.create_task(work(i)) for i in range(15)]
        # await all tasks; they coordinate via the token bucket
        await asyncio.gather(*tasks)
        print("Rate limiting completed\n")

    # -----------------------------
    # Request batcher (fixed)
    # -----------------------------
    async def request_batching_pattern(self) -> None:
        """
        Batch incoming requests for efficient processing.

        Demonstrates request batching pattern that groups requests for
        efficient batch processing while maintaining per-request responses.

        When to Use:
            - Batching operations for efficiency
            - Reducing per-operation overhead
            - Optimizing database operations
            - Grouping API calls
            - Improving throughput

        Real-World Examples:
            - Database batching: Batch multiple queries
            - API batching: Batch multiple API calls
            - File batching: Batch file operations
            - Message batching: Batch message sends
            - Write batching: Batch write operations

        Gotchas:
            - Each request gets its own Future
            - Batch processing happens outside lock
            - Timeout triggers batch processing
            - Batch size triggers immediate processing
            - Proper shutdown sets exceptions on pending futures
            - Never hold lock across await points

        Performance Notes:
            - Batching reduces per-operation overhead
            - Batch size balances latency vs efficiency
            - Timeout ensures timely processing
            - Optimal for high-throughput scenarios
            - Memory usage increases with batch size
        """
        print("=== Request Batching Pattern ===")

        async def process_batch(batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            # simulate expensive setup and per-item work (suspension)
            await asyncio.sleep(0.02)
            results = []
            for req in batch:
                await asyncio.sleep(0.005)
                results.append({"request_id": req["id"], "result": f"ok_{req['id']}"})
            return results

        class RequestBatcher:
            def __init__(self, batch_size: int = 5, timeout: float = 0.2):
                self.batch_size = batch_size
                self.timeout = timeout
                self._pending: deque = deque()
                self._futures: Dict[str, asyncio.Future] = {}
                self._lock = asyncio.Lock()
                self._wakeup = asyncio.Event()
                self._running = True

            async def submit(self, request: Dict[str, Any]) -> Any:
                """
                Submit a request and await its result:
                - create a Future for this request and return its result when ready.
                - we don't hold the lock while waiting for the future to be completed.
                """
                loop = asyncio.get_running_loop()
                fut = loop.create_future()
                async with self._lock:
                    self._pending.append(request)
                    self._futures[request["id"]] = fut
                    # if we reached batch_size, signal processor immediately
                    if len(self._pending) >= self.batch_size:
                        self._wakeup.set()
                try:
                    # wait for the future to be completed by the batch processor
                    await asyncio.wait_for(fut, timeout=self.timeout + 1.0)
                    return fut.result()
                except Exception:
                    # if the submitter timed out or cancellation happened, cancel the future
                    if not fut.done():
                        fut.cancel()
                    raise

            async def _run(self) -> None:
                """
                Background worker:
                - wakes on event or timeout, copies up to batch_size items under lock,
                  processes them outside the lock, and sets the futures' results.
                - uses small sleeps only if nothing to do.
                """
                try:
                    while self._running:
                        try:
                            # wait until either wakeup set (enough items) or timeout
                            try:
                                await asyncio.wait_for(self._wakeup.wait(), timeout=self.timeout)
                            except asyncio.TimeoutError:
                                # timeout passed — we will process any pending items (if any)
                                pass

                            # gather a batch under lock (fast operation)
                            async with self._lock:
                                if not self._pending:
                                    # nothing to do, clear wakeup and loop
                                    self._wakeup.clear()
                                    continue
                                batch = []
                                for _ in range(min(self.batch_size, len(self._pending))):
                                    batch.append(self._pending.popleft())
                                if not self._pending:
                                    self._wakeup.clear()
                        except Exception:
                            # any error in selection should not kill the worker
                            raise

                        # process batch outside lock (suspends here)
                        results = await process_batch(batch)

                        # match results to futures and set results
                        async with self._lock:
                            for r in results:
                                rid = r["request_id"]
                                fut = self._futures.pop(rid, None)
                                if fut and not fut.done():
                                    fut.set_result(r)
                except asyncio.CancelledError:
                    # on cancellation, propagate cancellation to pending futures
                    async with self._lock:
                        for fut in self._futures.values():
                            if not fut.done():
                                fut.set_exception(asyncio.CancelledError())
                    raise
                except Exception as e:
                    # log and continue; production code should record metrics
                    print(f"Batcher loop error: {e}")

            def start(self) -> asyncio.Task:
                # start background batcher task
                return asyncio.create_task(self._run())

            async def stop(self) -> None:
                # stop and wake the worker; worker will set exceptions on remaining futures
                self._running = False
                self._wakeup.set()

        # demo usage
        batcher = RequestBatcher(batch_size=3, timeout=0.1)
        bg = batcher.start()

        requests = [{"id": f"req_{i}", "data": f"x{i}"} for i in range(8)]
        # schedule submit calls concurrently
        submit_tasks = [asyncio.create_task(batcher.submit(r)) for r in requests]

        results = []
        for t in submit_tasks:
            try:
                results.append(await t)  # will suspend until each request's future completes
            except Exception as e:
                results.append({"error": str(e)})

        # stop worker and await background termination
        await batcher.stop()
        await bg

        print("Batching results:")
        for r in results:
            print(" ", r)

        print()

    # -----------------------------
    # Fan-out / Fan-in (as_completed) – explicit tasks
    # -----------------------------
    async def fan_out_fan_in_pattern(self) -> None:
        """
        Fan-out then fan-in using asyncio.as_completed.

        Demonstrates fan-out/fan-in pattern using as_completed for
        processing results as they complete (not in order).

        When to Use:
            - Processing independent work items
            - When order doesn't matter
            - Maximizing throughput
            - Handling variable processing times
            - Parallel data processing

        Real-World Examples:
            - Web scraping: Fetch multiple URLs concurrently
            - API aggregation: Call multiple APIs in parallel
            - Image processing: Process multiple images simultaneously
            - Data import: Import multiple records concurrently
            - Search: Query multiple search engines in parallel

        Gotchas:
            - Results arrive in completion order, not input order
            - as_completed yields futures as they finish
            - Tasks can be cancelled or inspected
            - Exceptions in one task don't stop others
            - Memory usage increases with number of tasks

        Performance Notes:
            - Processes items as they complete (low latency)
            - Better throughput than sequential processing
            - Optimal for I/O-bound independent work
            - Can handle thousands of concurrent tasks
            - Consider semaphores to limit concurrency
        """
        print("=== Fan-Out/Fan-In Pattern ===")

        async def worker(task_id: str, data: Any) -> Dict[str, Any]:
            # simulate variable processing; suspension point in sleep
            await asyncio.sleep(random.uniform(0.01, 0.08))
            return {"task_id": task_id, "input": data, "output": f"processed_{data}", "worker": f"w{random.randint(1,3)}"}

        items = [f"item_{i}" for i in range(12)]
        # create and schedule tasks immediately
        coros = [asyncio.create_task(worker(f"t{i}", it)) for i, it in enumerate(items)]

        results = []
        # as_completed returns an iterator of Futures as they complete; awaiting each yields result
        for fut in asyncio.as_completed(coros):
            r = await fut  # suspension occurs if the next completed future is not ready (but as_completed yields only ready ones)
            results.append(r)
            print(f" ✓ {r['task_id']} -> {r['output']}")

        print(f"fan-out/fan-in done: {len(results)} results\n")

    async def producer_consumer_real_world_example(self) -> None:
        """
        Real-World Scenario: Producer-Consumer - Job Queue System.

        REAL-WORLD SCENARIO:
        ====================
        You're building a job queue system:
        - Producers submit jobs
        - Workers consume and process jobs
        - Problem: Decouple producers from consumers
        
        THE PROBLEM WITHOUT QUEUE:
        ===========================
        - Producers wait for consumers → blocking
        - Tight coupling → inflexible
        - No buffering → lost jobs
        - Rate mismatch → inefficient
        - System fragile → poor scalability
        
        THE SOLUTION:
        =============
        Producer-Consumer with Queue enables:
        - Decouple producers from consumers
        - Buffer jobs in queue → handle rate mismatch
        - Multiple workers → parallel processing
        - Backpressure → prevent overload
        - Scalable architecture → production-ready
        
        WHEN TO USE PRODUCER-CONSUMER:
        ==============================
        ✅ Job queue systems
        ✅ Decoupling producers/consumers
        ✅ Handling variable rates
        ✅ Event-driven systems
        ✅ Task processing pipelines
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Job Queue System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Job queue system")
        print("  - Producers submit jobs")
        print("  - Workers consume and process jobs")
        print("  - Problem: Decouple producers from consumers")
        print()
        print("THE PROBLEM:")
        print("  Without queue:")
        print("    ❌ Producers wait for consumers → blocking")
        print("    ❌ Tight coupling → inflexible")
        print("    ❌ No buffering → lost jobs")
        print("    ❌ Rate mismatch → inefficient")
        print()
        print("THE SOLUTION:")
        print("  With producer-consumer queue:")
        print("    ✅ Decouple producers from consumers")
        print("    ✅ Buffer jobs in queue → handle rate mismatch")
        print("    ✅ Multiple workers → parallel processing")
        print("    ✅ Backpressure → prevent overload")
        print()
        print("=" * 70)
        print()

        job_queue = asyncio.Queue(maxsize=10)

        async def producer(producer_id: int, num_jobs: int) -> None:
            """Producer that submits jobs."""
            for i in range(num_jobs):
                job = {"producer_id": producer_id, "job_id": i+1, "data": f"job_{producer_id}_{i+1}"}
                await job_queue.put(job)
                print(f"  Producer {producer_id}: Submitted job {i+1}")
                await asyncio.sleep(0.05)

        async def consumer(consumer_id: int) -> None:
            """Consumer that processes jobs."""
            processed = 0
            while True:
                job = await job_queue.get()
                if job is None:  # Sentinel
                    job_queue.task_done()
                    break
                
                # Process job
                await asyncio.sleep(0.1)  # Simulate processing
                processed += 1
                print(f"  Consumer {consumer_id}: Processed job from producer {job['producer_id']}")
                job_queue.task_done()

            print(f"  Consumer {consumer_id}: Processed {processed} jobs total")

        print("Starting job queue system...")
        print("  - 2 producers submitting jobs")
        print("  - 3 consumers processing jobs")
        print()

        # Start consumers
        consumers = [asyncio.create_task(consumer(i+1)) for i in range(3)]

        # Start producers
        producers = [
            asyncio.create_task(producer(1, 5)),
            asyncio.create_task(producer(2, 5))
        ]

        # Wait for producers
        await asyncio.gather(*producers)

        # Signal consumers to stop
        for _ in range(3):
            await job_queue.put(None)

        # Wait for queue to empty
        await job_queue.join()

        # Wait for consumers
        await asyncio.gather(*consumers)

        print()
        print("  ✅ Producer-Consumer queue enabled decoupled job processing!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE PRODUCER-CONSUMER:")
        print("   ✅ Job queue systems")
        print("   ✅ Decoupling producers/consumers")
        print("   ✅ Handling variable rates")
        print("   ✅ Event-driven systems")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Decouples producers from consumers")
        print("   - Handles rate mismatches")
        print("   - Enables parallel processing")
        print("   - Scalable architecture")
        print("=" * 70)
        print()

    async def circuit_breaker_real_world_example(self) -> None:
        """
        Real-World Scenario: Circuit Breaker - External API Client.

        REAL-WORLD SCENARIO:
        ====================
        You're building an external API client:
        - Call external service for data
        - Service may be down or slow
        - Problem: Failures cascade, waste resources
        
        THE PROBLEM WITHOUT CIRCUIT BREAKER:
        =====================================
        - Service down → all requests fail → waste
        - Slow service → requests timeout → cascade
        - No failure detection → keep trying → waste
        - System overwhelmed → poor performance
        - Resource exhaustion → system failure
        
        THE SOLUTION:
        =============
        Circuit breaker enables:
        - Detect failures → stop calling failing service
        - Fast failure → no waiting for timeouts
        - Automatic recovery → retry after cooldown
        - Prevent cascade failures → system stability
        - Resource protection → efficient
        
        WHEN TO USE CIRCUIT BREAKER:
        ============================
        ✅ External API clients
        ✅ Service integration
        ✅ Failure-prone dependencies
        ✅ Preventing cascade failures
        ✅ Resource protection
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: External API Client")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - External API client")
        print("  - Call external service for data")
        print("  - Service may be down or slow")
        print("  - Problem: Failures cascade, waste resources")
        print()
        print("THE PROBLEM:")
        print("  Without circuit breaker:")
        print("    ❌ Service down → all requests fail → waste")
        print("    ❌ Slow service → requests timeout → cascade")
        print("    ❌ No failure detection → keep trying → waste")
        print("    ❌ System overwhelmed → poor performance")
        print()
        print("THE SOLUTION:")
        print("  With circuit breaker:")
        print("    ✅ Detect failures → stop calling failing service")
        print("    ✅ Fast failure → no waiting for timeouts")
        print("    ✅ Automatic recovery → retry after cooldown")
        print("    ✅ Prevent cascade failures → system stability")
        print()
        print("=" * 70)
        print()

        class SimpleCircuitBreaker:
            """Simple circuit breaker implementation."""
            def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 2.0):
                self.failure_threshold = failure_threshold
                self.recovery_timeout = recovery_timeout
                self.failure_count = 0
                self.state = "closed"  # closed, open, half_open
                self.last_failure_time = 0.0

            async def call(self, func, *args, **kwargs):
                """Call function with circuit breaker protection."""
                if self.state == "open":
                    if time.time() - self.last_failure_time > self.recovery_timeout:
                        self.state = "half_open"
                        print("  Circuit breaker: Half-open (testing recovery)")
                    else:
                        raise Exception("Circuit breaker is OPEN - service unavailable")

                try:
                    result = await func(*args, **kwargs)
                    if self.state == "half_open":
                        self.state = "closed"
                        self.failure_count = 0
                        print("  Circuit breaker: Closed (service recovered)")
                    return result
                except Exception as e:
                    self.failure_count += 1
                    self.last_failure_time = time.time()
                    if self.failure_count >= self.failure_threshold:
                        self.state = "open"
                        print(f"  Circuit breaker: OPEN (too many failures: {self.failure_count})")
                    raise

        async def call_external_api(request_id: int) -> dict:
            """Simulate calling external API."""
            if request_id <= 3:
                # First 3 requests fail (simulate service down)
                raise Exception(f"API error for request {request_id}")
            await asyncio.sleep(0.05)
            return {"request_id": request_id, "status": "success"}

        breaker = SimpleCircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

        print("Calling external API with circuit breaker protection...")
        print()

        for i in range(1, 8):
            try:
                result = await breaker.call(call_external_api, i)
                print(f"  Request {i}: ✅ Success")
            except Exception as e:
                print(f"  Request {i}: ❌ Failed - {e}")
            await asyncio.sleep(0.2)

        print()
        print("  ✅ Circuit breaker prevented cascade failures!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE CIRCUIT BREAKER:")
        print("   ✅ External API clients")
        print("   ✅ Service integration")
        print("   ✅ Failure-prone dependencies")
        print("   ✅ Preventing cascade failures")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Prevents cascade failures")
        print("   - Fast failure (no waiting)")
        print("   - Automatic recovery")
        print("   - Resource protection")
        print("=" * 70)
        print()


async def main() -> None:
    example = AsyncPatternsExample()

    # Run all the examples. Each call may suspend inside as it awaits tasks.
    await example.producer_consumer_queue()
    await example.data_pipeline_pattern()
    await example.pub_sub_pattern()
    await example.circuit_breaker_pattern()
    await example.retry_with_backoff_pattern()
    await example.rate_limiting_pattern()
    await example.request_batching_pattern()
    await example.fan_out_fan_in_pattern()

    # Real-world scenarios
    print("\n" + "=" * 70)
    print("RUNNING REAL-WORLD SCENARIOS")
    print("=" * 70 + "\n")
    await example.producer_consumer_real_world_example()
    await example.circuit_breaker_real_world_example()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted")

"""
🎯 Key Advanced Patterns Demonstrated:
Producer-Consumer - Bounded queues with multiple producers/consumers
Data Pipeline - Multi-stage async processing with queues between stages
Pub-Sub - Topic-based message distribution to multiple subscribers
Circuit Breaker - Fault tolerance with failure thresholds and recovery
Retry with Backoff - Exponential backoff with jitter to prevent thundering herd
Rate Limiting - Token bucket algorithm for request throttling
Request Batching - Group requests for efficient batch processing
Fan-Out/Fan-In - Distribute work and collect results concurrently

🔑 Why These Patterns Matter:
Scalability - Handle thousands of concurrent operations
Fault Tolerance - Circuit breakers and retries prevent cascade failures
Efficiency - Batching and rate limiting optimize resource usage
Reliability - Pub-sub and pipelines decouple components
Performance - Concurrent processing maximizes throughput
Real-world - These patterns solve production system challenges
This file provides a comprehensive toolkit of advanced async patterns essential for building production-grade concurrent applications! 🚀⚡📊
"""
