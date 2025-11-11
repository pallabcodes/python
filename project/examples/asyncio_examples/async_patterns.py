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
    """Collection of robust, production-aware asyncio patterns."""

    # -----------------------------
    # Producer / Consumer (bounded)
    # -----------------------------
    async def producer_consumer_queue(self) -> None:
        """Producer/consumer with bounded queue, explicit sentinels and join.

        Key points:
        - Queue(maxsize) provides backpressure automatically on put().
        - Each consumer expects exactly one sentinel to terminate.
        - Use task_done()/join() to know when all real work items are processed.
        """
        print("=== Producer-Consumer with Queue ===")

        queue: asyncio.Queue = asyncio.Queue(maxsize=3)
        num_producers = 2
        num_consumers = 2

        async def producer(pid: int, q: asyncio.Queue, n: int = 5) -> None:
            for i in range(n):
                item = f"Item-P{pid}-{i+1}"
                await q.put(item)  # may suspend when queue is full (backpressure)
                print(f"📦 Producer{pid}: produced {item}")
                await asyncio.sleep(random.uniform(0.05, 0.15))

            print(f"📦 Producer{pid}: done producing")

        async def consumer(cid: int, q: asyncio.Queue) -> None:
            processed = 0
            while True:
                item = await q.get()  # suspend until available
                try:
                    if item is None:  # sentinel -> exit
                        print(f"🛑 Consumer{cid}: received sentinel")
                        return

                    # simulate processing
                    await asyncio.sleep(random.uniform(0.1, 0.25))
                    processed += 1
                    print(f"🍽️  Consumer{cid}: processed {item}")

                finally:
                    # Always mark task done for items taken from queue
                    q.task_done()

        # Start consumers
        consumer_tasks = [asyncio.create_task(consumer(i + 1, queue)) for i in range(num_consumers)]

        # Start producers
        producer_tasks = [asyncio.create_task(producer(i + 1, queue)) for i in range(num_producers)]

        # Wait for producers to finish producing
        await asyncio.gather(*producer_tasks)

        # All producers finished; enqueue one sentinel per consumer to shut them down
        for _ in range(num_consumers):
            await queue.put(None)

        # Wait until all real items have been processed (task_done matched puts excluding finish sentinels)
        await queue.join()

        # Wait for consumers to exit
        await asyncio.gather(*consumer_tasks)

        print("Producer-consumer pattern completed!\n")

    # -----------------------------
    # Pipeline (multi-stage)
    # -----------------------------
    async def data_pipeline_pattern(self) -> None:
        """Multi-stage pipeline using queues and explicit sentinel forwarding.

        Each stage is independent; using sentinels we implement clean shutdown.
        """
        print("=== Data Processing Pipeline ===")

        async def data_source() -> AsyncGenerator[Dict[str, Any], None]:
            items = [
                {"id": 1, "raw_value": 10, "category": "A"},
                {"id": 2, "raw_value": 25, "category": "B"},
                {"id": 3, "raw_value": 15, "category": "A"},
                {"id": 4, "raw_value": 30, "category": "C"},
                {"id": 5, "raw_value": 20, "category": "B"},
            ]
            for it in items:
                await asyncio.sleep(0.05)
                yield it

        async def stage1_filter(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
            results = []
            totals: Dict[str, Dict[str, float]] = {}
            while True:
                item = await q.get()
                if item is None:
                    q.task_done()
                    break
                try:
                    results.append(item)
                    cat = item["category"]
                    totals.setdefault(cat, {"count": 0, "total_value": 0.0})
                    totals[cat]["count"] += 1
                    totals[cat]["total_value"] += item["transformed_value"]
                finally:
                    q.task_done()

            # calculate averages
            for cat, stats in totals.items():
                stats["avg_value"] = stats["total_value"] / stats["count"]

            return {"total_processed": len(results), "results": results, "category_stats": totals}

        q1: asyncio.Queue = asyncio.Queue()
        q2: asyncio.Queue = asyncio.Queue()

        async def pipeline_stage1():
            async for item in data_source():
                filtered = await stage1_filter(item)
                if filtered:
                    await q1.put(filtered)

            # done producing for stage1
            await q1.put(None)

        async def pipeline_stage2():
            while True:
                item = await q1.get()
                try:
                    if item is None:
                        # forward sentinel and exit
                        await q2.put(None)
                        return
                    transformed = await stage2_transform(item)
                    await q2.put(transformed)
                finally:
                    q1.task_done()

        # run stages
        t1 = asyncio.create_task(pipeline_stage1())
        t2 = asyncio.create_task(pipeline_stage2())
        t3 = asyncio.create_task(stage3_aggregate(q2))

        await t1
        # ensure all items from q1 processed and forwarded
        await q1.join()
        await t2

        # wait for aggregation
        final = await t3

        print("\n📊 Pipeline Results:")
        print(f"  Total processed: {final['total_processed']}")
        for cat, stats in final["category_stats"].items():
            print(f"    {cat}: count={stats['count']}, avg={stats['avg_value']:.1f}")
        print()

    # -----------------------------
    # Pub/Sub (copy subscribers, avoid long lock hold)
    # -----------------------------
    async def pub_sub_pattern(self) -> None:
        print("=== Publish-Subscribe Pattern ===")

        class AsyncPubSub:
            def __init__(self):
                self._subscribers: Dict[str, List[asyncio.Queue]] = {}
                self._lock = asyncio.Lock()

            async def subscribe(self, topic: str) -> asyncio.Queue:
                q = asyncio.Queue()
                async with self._lock:
                    self._subscribers.setdefault(topic, []).append(q)
                return q

            async def unsubscribe(self, topic: str, q: asyncio.Queue) -> None:
                async with self._lock:
                    if topic in self._subscribers and q in self._subscribers[topic]:
                        self._subscribers[topic].remove(q)

            async def publish(self, topic: str, message: Any) -> None:
                # Copy subscriber list under lock then release; do not await while holding lock.
                async with self._lock:
                    subs = list(self._subscribers.get(topic, []))

                if not subs:
                    return

                # Publish concurrently but outside the lock
                await asyncio.gather(*(s.put(message) for s in subs))

        async def publisher(pubsub: AsyncPubSub, topic: str) -> None:
            for m in ("Message 1", "Message 2", "Message 3", "END"):
                await pubsub.publish(topic, m)
                await asyncio.sleep(0.05)

        async def subscriber(name: str, pubsub: AsyncPubSub, topic: str) -> None:
            q = await pubsub.subscribe(topic)
            try:
                while True:
                    m = await q.get()
                    try:
                        if m == "END":
                            return
                        print(f"📨 {name} got: {m}")
                        await asyncio.sleep(0.02)
                    finally:
                        q.task_done()
            finally:
                await pubsub.unsubscribe(topic, q)

        pubsub = AsyncPubSub()
        pub = asyncio.create_task(publisher(pubsub, "news"))
        subs = [asyncio.create_task(subscriber(f"S{i+1}", pubsub, "news")) for i in range(3)]

        await asyncio.gather(pub, *subs)
        print("Pub-sub pattern completed!\n")

    # -----------------------------
    # Circuit breaker (robust)
    # -----------------------------
    async def circuit_breaker_pattern(self) -> None:
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
                # Read-only check under lock
                async with self._lock:
                    if self.state == "open":
                        if self.last_failure_time and (time.time() - self.last_failure_time) >= self.recovery_timeout:
                            self.state = "half-open"
                        else:
                            raise RuntimeError("Circuit is open")

                try:
                    result = await func(*args, **kwargs)
                except Exception as e:
                    # on failure increment counter
                    async with self._lock:
                        self.failure_count += 1
                        self.last_failure_time = time.time()
                        if self.failure_count >= self.failure_threshold:
                            self.state = "open"
                    raise
                else:
                    # on success reset if needed
                    async with self._lock:
                        if self.state == "half-open":
                            self.state = "closed"
                            self.failure_count = 0
                        else:
                            self.failure_count = 0
                    return result

        async def unreliable(call_id: str) -> str:
            if random.random() < 0.35:
                await asyncio.sleep(0.02)
                raise ConnectionError(call_id)
            await asyncio.sleep(0.03)
            return f"ok:{call_id}"

        cb = AsyncCircuitBreaker(failure_threshold=2, recovery_timeout=0.5)
        for i in range(10):
            cid = f"call_{i+1}"
            try:
                r = await cb.call(unreliable, cid)
                print(f"  ✅ {cid}: {r}")
            except Exception as e:
                print(f"  ❌ {cid}: {e}")
            await asyncio.sleep(0.05)

        print()

    # -----------------------------
    # Retry with exponential backoff
    # -----------------------------
    async def retry_with_backoff_pattern(self) -> None:
        print("=== Retry with Backoff Pattern ===")

        async def unreliable(attempt: int) -> str:
            if attempt < 3:
                raise ConnectionError(f"attempt {attempt}")
            return f"ok-{attempt}"

        async def retry(coro_factory, max_attempts: int = 5, base_delay: float = 0.05, max_delay: float = 1.0):
            for attempt in range(1, max_attempts + 1):
                try:
                    return await coro_factory(attempt)
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    jitter = delay * 0.1 * random.random()
                    to_sleep = delay + jitter
                    print(f"  attempt={attempt} failed: {e}; backing off {to_sleep:.3f}s")
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
        print("=== Rate Limiting Pattern ===")

        class TokenBucket:
            def __init__(self, rate: float, capacity: int):
                self.rate = rate
                self.capacity = float(capacity)
                self.tokens = float(capacity)
                self.last = time.monotonic()
                self._lock = asyncio.Lock()

            async def _refill(self) -> None:
                now = time.monotonic()
                elapsed = now - self.last
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last = now

            async def acquire(self, tokens: int = 1) -> bool:
                async with self._lock:
                    await self._refill()
                    if self.tokens >= tokens:
                        self.tokens -= tokens
                        return True
                    return False

            async def wait(self, tokens: int = 1) -> None:
                while True:
                    async with self._lock:
                        await self._refill()
                        if self.tokens >= tokens:
                            self.tokens -= tokens
                            return
                        # compute precise sleep until tokens available
                        need = tokens - self.tokens
                        sleep_time = need / self.rate if self.rate > 0 else 0.1
                    await asyncio.sleep(max(0.001, sleep_time))

        limiter = TokenBucket(rate=10, capacity=5)
        async def work(i: int):
            await limiter.wait(1)
            print(f"🚀 task {i} running")
            await asyncio.sleep(0.01)

        tasks = [asyncio.create_task(work(i)) for i in range(15)]
        await asyncio.gather(*tasks)
        print("Rate limiting completed\n")

    # -----------------------------
    # Request batcher (fixed)
    # -----------------------------
    async def request_batching_pattern(self) -> None:
        print("=== Request Batching Pattern ===")

        async def process_batch(batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            await asyncio.sleep(0.02)  # simulate batch overhead
            results = []
            for req in batch:
                await asyncio.sleep(0.005)  # per-item work
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
                loop = asyncio.get_running_loop()
                fut = loop.create_future()
                async with self._lock:
                    self._pending.append(request)
                    self._futures[request["id"]] = fut
                    if len(self._pending) >= self.batch_size:
                        self._wakeup.set()
                try:
                    # wait either until our future is set by batch processor or timeout
                    await asyncio.wait_for(fut, timeout=self.timeout + 1.0)
                    return fut.result()
                except Exception:
                    # If timeout or cancellation, try best-effort: return partial or raise
                    if not fut.done():
                        fut.cancel()
                    raise

            async def _run(self) -> None:
                while self._running:
                    try:
                        # Wait for wakeup or timeout
                        try:
                            await asyncio.wait_for(self._wakeup.wait(), timeout=self.timeout)
                        except asyncio.TimeoutError:
                            pass

                        async with self._lock:
                            if not self._pending:
                                self._wakeup.clear()
                                continue
                            # build a batch up to batch_size
                            batch = []
                            for _ in range(min(self.batch_size, len(self._pending))):
                                batch.append(self._pending.popleft())
                            if not self._pending:
                                self._wakeup.clear()

                        # process batch outside lock
                        results = await process_batch(batch)

                        # set results back to futures
                        async with self._lock:
                            for r in results:
                                rid = r["request_id"]
                                fut = self._futures.pop(rid, None)
                                if fut and not fut.done():
                                    fut.set_result(r)
                    except Exception as e:
                        # log and continue; ensure we don't die silently
                        print(f"Batcher loop error: {e}")

            def start(self) -> asyncio.Task:
                return asyncio.create_task(self._run())

            async def stop(self) -> None:
                self._running = False
                self._wakeup.set()

        batcher = RequestBatcher(batch_size=3, timeout=0.1)
        bg = batcher.start()

        requests = [{"id": f"req_{i}", "data": f"x{i}"} for i in range(8)]
        submit_tasks = [asyncio.create_task(batcher.submit(r)) for r in requests]

        results = []
        for t in submit_tasks:
            try:
                results.append(await t)
            except Exception as e:
                results.append({"error": str(e)})

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
        print("=== Fan-Out/Fan-In Pattern ===")

        async def worker(task_id: str, data: Any) -> Dict[str, Any]:
            await asyncio.sleep(random.uniform(0.01, 0.08))
            return {"task_id": task_id, "input": data, "output": f"processed_{data}", "worker": f"w{random.randint(1,3)}"}

        items = [f"item_{i}" for i in range(12)]
        coros = [asyncio.create_task(worker(f"t{i}", it)) for i, it in enumerate(items)]

        results = []
        for fut in asyncio.as_completed(coros):
            r = await fut
            results.append(r)
            print(f" ✓ {r['task_id']} -> {r['output']}")

        print(f"fan-out/fan-in done: {len(results)} results\n")


async def main() -> None:
    example = AsyncPatternsExample()

    await example.producer_consumer_queue()
    await example.data_pipeline_pattern()
    await example.pub_sub_pattern()
    await example.circuit_breaker_pattern()
    await example.retry_with_backoff_pattern()
    await example.rate_limiting_pattern()
    await example.request_batching_pattern()
    await example.fan_out_fan_in_pattern()


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
