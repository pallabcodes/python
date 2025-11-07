"""
Real-World Hybrid Applications.

This module demonstrates complete hybrid concurrency applications:
- Web Server: Handles both I/O and CPU intensive requests
- Data Pipeline: Multi-stage processing with different concurrency needs
- Database Hybrid: Fast queries + heavy analytics

Key patterns:
- Application-level hybrid architecture
- Request routing based on workload characteristics
- Resource isolation and QoS
- Monitoring and adaptive scaling
"""

import asyncio
import threading
import multiprocessing
import concurrent.futures
import time
import logging
import json
import random
from typing import Any, Callable, List, Dict, Optional, Union, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class Request:
    """Represents a web request."""
    request_id: str
    endpoint: str
    method: str
    data: Dict[str, Any]
    priority: int = 1
    submitted_time: float = field(default_factory=time.time)


@dataclass
class RequestResult:
    """Result of processing a request."""
    request_id: str
    status_code: int
    response_data: Any
    processing_time: float
    worker_type: str


class WebServerHybrid:
    """
    Hybrid web server that intelligently routes requests based on workload.

    Architecture:
    - AsyncIO for I/O-bound requests (API calls, database queries)
    - Thread pools for moderate CPU work (data processing, validation)
    - Process pools for heavy CPU work (ML inference, complex calculations)
    - Priority-based request queuing
    """

    def __init__(self,
                 host: str = "localhost",
                 port: int = 8080,
                 max_threads: int = 8,
                 max_processes: int = 2):
        self.host = host
        self.port = port
        self.max_threads = max_threads
        self.max_processes = max_processes

        # Executors
        self._thread_executor: Optional[ThreadPoolExecutor] = None
        self._process_executor: Optional[ProcessPoolExecutor] = None

        # Request routing
        self._routes: Dict[str, Dict[str, Callable]] = {}
        self._running = False

        # Metrics
        self._request_count = 0
        self._metrics: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

        # Request queue for priority handling
        self._request_queue: asyncio.Queue = asyncio.Queue()
        self._processing_tasks: List[asyncio.Task] = []

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    def route(self, path: str, methods: List[str] = None):
        """Decorator to register routes."""
        methods = methods or ["GET"]

        def decorator(func):
            if path not in self._routes:
                self._routes[path] = {}

            for method in methods:
                self._routes[path][method.upper()] = func

            return func
        return decorator

    async def start(self):
        """Start the hybrid web server."""
        if self._running:
            return

        # Initialize executors
        self._thread_executor = ThreadPoolExecutor(
            max_workers=self.max_threads,
            thread_name_prefix="web-thread"
        )
        self._process_executor = ProcessPoolExecutor(
            max_workers=self.max_processes
        )

        self._running = True

        # Start request processors
        for i in range(4):  # 4 concurrent request processors
            task = asyncio.create_task(self._process_requests())
            self._processing_tasks.append(task)

        logger.info(f"Started WebServerHybrid on {self.host}:{self.port}")

    async def stop(self):
        """Stop the web server."""
        if not self._running:
            return

        self._running = False

        # Cancel processing tasks
        for task in self._processing_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._processing_tasks, return_exceptions=True)

        # Shutdown executors
        if self._thread_executor:
            self._thread_executor.shutdown(wait=True)
        if self._process_executor:
            self._process_executor.shutdown(wait=True)

        logger.info("Stopped WebServerHybrid")

    async def handle_request(self, request: Request) -> RequestResult:
        """Handle an incoming request."""
        start_time = time.time()

        try:
            # Route the request
            if request.endpoint not in self._routes:
                return RequestResult(
                    request_id=request.request_id,
                    status_code=404,
                    response_data={"error": "Not found"},
                    processing_time=time.time() - start_time,
                    worker_type="routing"
                )

            method_routes = self._routes[request.endpoint]
            if request.method.upper() not in method_routes:
                return RequestResult(
                    request_id=request.request_id,
                    status_code=405,
                    response_data={"error": "Method not allowed"},
                    processing_time=time.time() - start_time,
                    worker_type="routing"
                )

            handler = method_routes[request.method.upper()]

            # Analyze workload and choose execution model
            workload_type = self._analyze_request_workload(request)

            if workload_type == "cpu_heavy":
                # Use process pool for heavy CPU work
                loop = asyncio.get_event_loop()
                response_data = await loop.run_in_executor(
                    self._process_executor, handler, request
                )
                worker_type = "process"
            elif workload_type == "cpu_light":
                # Use thread pool for light CPU work
                loop = asyncio.get_event_loop()
                response_data = await loop.run_in_executor(
                    self._thread_executor, handler, request
                )
                worker_type = "thread"
            else:
                # Use asyncio for I/O work
                response_data = await handler(request)
                worker_type = "asyncio"

            processing_time = time.time() - start_time

            # Record metrics
            with self._lock:
                self._request_count += 1
                self._metrics.append({
                    "request_id": request.request_id,
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "processing_time": processing_time,
                    "worker_type": worker_type,
                    "status_code": 200
                })

            return RequestResult(
                request_id=request.request_id,
                status_code=200,
                response_data=response_data,
                processing_time=processing_time,
                worker_type=worker_type
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Request {request.request_id} failed: {e}")

            with self._lock:
                self._metrics.append({
                    "request_id": request.request_id,
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "processing_time": processing_time,
                    "worker_type": "error",
                    "status_code": 500
                })

            return RequestResult(
                request_id=request.request_id,
                status_code=500,
                response_data={"error": str(e)},
                processing_time=processing_time,
                worker_type="error"
            )

    def _analyze_request_workload(self, request: Request) -> str:
        """Analyze request to determine workload type."""
        # Simple heuristic based on endpoint and data size
        endpoint = request.endpoint.lower()

        if any(keyword in endpoint for keyword in ['calculate', 'process', 'ml', 'inference']):
            return "cpu_heavy"
        elif any(keyword in endpoint for keyword in ['validate', 'transform', 'filter']):
            return "cpu_light"
        elif len(str(request.data)) > 1000:  # Large payload
            return "cpu_light"
        else:
            return "io"

    async def _process_requests(self):
        """Process requests from the queue."""
        while self._running:
            try:
                request = await asyncio.wait_for(
                    self._request_queue.get(), timeout=0.1
                )
                result = await self.handle_request(request)
                # In real implementation, send result back to client
                logger.debug(f"Processed request {request.request_id}: {result.status_code}")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Request processing error: {e}")

    def get_server_stats(self) -> Dict[str, Any]:
        """Get server performance statistics."""
        if not self._metrics:
            return {"message": "No metrics available"}

        processing_times = [m["processing_time"] for m in self._metrics]
        status_codes = [m["status_code"] for m in self._metrics]

        worker_types = defaultdict(int)
        for m in self._metrics:
            worker_types[m["worker_type"]] += 1

        return {
            "total_requests": len(self._metrics),
            "avg_processing_time": statistics.mean(processing_times),
            "p95_processing_time": statistics.quantiles(processing_times, n=20)[18] if len(processing_times) >= 20 else max(processing_times),
            "success_rate": sum(1 for s in status_codes if s < 400) / len(status_codes),
            "worker_distribution": dict(worker_types),
            "requests_per_second": len(self._metrics) / (time.time() - self._metrics[0]["processing_time"]) if self._metrics else 0
        }


class DataPipelineHybrid:
    """
    Hybrid data processing pipeline with multiple stages.

    Pipeline stages:
    1. Ingestion (AsyncIO) - Handle incoming data streams
    2. Validation (Threading) - Data quality checks
    3. Processing (Multiprocessing) - Heavy computation
    4. Aggregation (Threading) - Combine results
    5. Storage (AsyncIO) - Write to storage
    """

    def __init__(self, num_workers: Dict[str, int] = None):
        self.num_workers = num_workers or {
            "ingestion": 4,
            "validation": 6,
            "processing": 2,
            "aggregation": 4,
            "storage": 4
        }

        # Pipeline queues
        self._queues: Dict[str, asyncio.Queue] = {}
        self._running = False

        # Executors
        self._thread_executor: Optional[ThreadPoolExecutor] = None
        self._process_executor: Optional[ProcessPoolExecutor] = None

        # Pipeline tasks
        self._pipeline_tasks: List[asyncio.Task] = []

        # Metrics
        self._processed_items = 0
        self._stage_metrics: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start the data pipeline."""
        if self._running:
            return

        # Initialize queues
        stages = ["ingestion", "validation", "processing", "aggregation", "storage"]
        for stage in stages:
            self._queues[stage] = asyncio.Queue(maxsize=1000)

        # Initialize executors
        self._thread_executor = ThreadPoolExecutor(
            max_workers=self.num_workers["validation"] + self.num_workers["aggregation"],
            thread_name_prefix="pipeline-thread"
        )
        self._process_executor = ProcessPoolExecutor(
            max_workers=self.num_workers["processing"]
        )

        self._running = True

        # Start pipeline stages
        self._pipeline_tasks = [
            asyncio.create_task(self._ingestion_stage()),
            asyncio.create_task(self._validation_stage()),
            asyncio.create_task(self._processing_stage()),
            asyncio.create_task(self._aggregation_stage()),
            asyncio.create_task(self._storage_stage()),
        ]

        logger.info("Started DataPipelineHybrid")

    async def stop(self):
        """Stop the data pipeline."""
        if not self._running:
            return

        self._running = False

        # Cancel pipeline tasks
        for task in self._pipeline_tasks:
            task.cancel()

        await asyncio.gather(*self._pipeline_tasks, return_exceptions=True)

        # Shutdown executors
        if self._thread_executor:
            self._thread_executor.shutdown(wait=True)
        if self._process_executor:
            self._process_executor.shutdown(wait=True)

        logger.info("Stopped DataPipelineHybrid")

    async def submit_data(self, data: Any) -> str:
        """Submit data to the pipeline."""
        item_id = f"item_{int(time.time() * 1000000)}"
        await self._queues["ingestion"].put((item_id, data))
        return item_id

    async def _ingestion_stage(self):
        """Stage 1: AsyncIO-based data ingestion."""
        while self._running:
            try:
                item_id, data = await self._queues["ingestion"].get()
                start_time = time.time()

                # Simulate async I/O ingestion
                await asyncio.sleep(0.01)  # Simulate network I/O

                processing_time = time.time() - start_time
                with self._lock:
                    self._stage_metrics["ingestion"].append(processing_time)

                # Pass to validation
                await self._queues["validation"].put((item_id, data))
                self._queues["ingestion"].task_done()

            except Exception as e:
                logger.error(f"Ingestion stage error: {e}")

    async def _validation_stage(self):
        """Stage 2: Thread-based data validation."""
        loop = asyncio.get_event_loop()

        while self._running:
            try:
                item_id, data = await self._queues["validation"].get()
                start_time = time.time()

                # Run validation in thread pool
                validated_data = await loop.run_in_executor(
                    self._thread_executor, self._validate_data, item_id, data
                )

                processing_time = time.time() - start_time
                with self._lock:
                    self._stage_metrics["validation"].append(processing_time)

                # Pass to processing
                await self._queues["processing"].put((item_id, validated_data))
                self._queues["validation"].task_done()

            except Exception as e:
                logger.error(f"Validation stage error: {e}")

    async def _processing_stage(self):
        """Stage 3: Process-based heavy computation."""
        loop = asyncio.get_event_loop()

        while self._running:
            try:
                item_id, data = await self._queues["processing"].get()
                start_time = time.time()

                # Run heavy processing in process pool
                processed_data = await loop.run_in_executor(
                    self._process_executor, self._process_data, item_id, data
                )

                processing_time = time.time() - start_time
                with self._lock:
                    self._stage_metrics["processing"].append(processing_time)

                # Pass to aggregation
                await self._queues["aggregation"].put((item_id, processed_data))
                self._queues["processing"].task_done()

            except Exception as e:
                logger.error(f"Processing stage error: {e}")

    async def _aggregation_stage(self):
        """Stage 4: Thread-based result aggregation."""
        loop = asyncio.get_event_loop()

        while self._running:
            try:
                item_id, data = await self._queues["aggregation"].get()
                start_time = time.time()

                # Run aggregation in thread pool
                aggregated_data = await loop.run_in_executor(
                    self._thread_executor, self._aggregate_data, item_id, data
                )

                processing_time = time.time() - start_time
                with self._lock:
                    self._stage_metrics["aggregation"].append(processing_time)

                # Pass to storage
                await self._queues["storage"].put((item_id, aggregated_data))
                self._queues["aggregation"].task_done()

            except Exception as e:
                logger.error(f"Aggregation stage error: {e}")

    async def _storage_stage(self):
        """Stage 5: AsyncIO-based data storage."""
        while self._running:
            try:
                item_id, data = await self._queues["storage"].get()
                start_time = time.time()

                # Simulate async storage I/O
                await asyncio.sleep(0.02)  # Simulate storage I/O

                processing_time = time.time() - start_time
                with self._lock:
                    self._stage_metrics["storage"].append(processing_time)
                    self._processed_items += 1

                self._queues["storage"].task_done()
                logger.debug(f"Stored item {item_id}")

            except Exception as e:
                logger.error(f"Storage stage error: {e}")

    def _validate_data(self, item_id: str, data: Any) -> Any:
        """Validate data (runs in thread pool)."""
        # Simulate validation work
        time.sleep(0.005)
        if isinstance(data, dict) and "error" in data:
            raise ValueError(f"Invalid data in {item_id}")
        return data

    def _process_data(self, item_id: str, data: Any) -> Any:
        """Process data (runs in process pool)."""
        import math

        # Simulate heavy computation
        if isinstance(data, dict) and "values" in data:
            result = sum(math.sin(x) * math.cos(x) for x in data["values"][:100])
            return {"processed": result, "item_id": item_id}
        else:
            result = sum(math.sin(i) * math.cos(i) for i in range(1000))
            return {"processed": result, "item_id": item_id}

    def _aggregate_data(self, item_id: str, data: Any) -> Any:
        """Aggregate data (runs in thread pool)."""
        # Simulate aggregation work
        time.sleep(0.003)
        return {
            "final_result": data.get("processed", 0) * 2,
            "item_id": item_id,
            "aggregated_at": time.time()
        }

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline performance statistics."""
        with self._lock:
            stats = {}
            for stage, times in self._stage_metrics.items():
                if times:
                    stats[stage] = {
                        "items_processed": len(times),
                        "avg_time": statistics.mean(times),
                        "total_time": sum(times)
                    }

            return {
                "total_items_processed": self._processed_items,
                "stage_stats": stats,
                "throughput": self._processed_items / sum(sum(times) for times in self._stage_metrics.values()) if self._stage_metrics else 0
            }


class DatabaseHybrid:
    """
    Hybrid database system handling both fast queries and heavy analytics.

    Architecture:
    - Fast queries: AsyncIO for I/O-bound database access
    - Analytics: Process pools for CPU-intensive computations
    - Caching: Thread pools for cache operations
    """

    def __init__(self, max_fast_queries: int = 10, max_analytics: int = 2):
        self.max_fast_queries = max_fast_queries
        self.max_analytics = max_analytics

        # Simulators for different operations
        self._data_store: Dict[str, Any] = {}
        self._cache: Dict[str, Any] = {}

        # Executors
        self._thread_executor: Optional[ThreadPoolExecutor] = None
        self._process_executor: Optional[ProcessPoolExecutor] = None
        self._running = False

        # Metrics
        self._query_metrics: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

        # Initialize sample data
        self._initialize_sample_data()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    def _initialize_sample_data(self):
        """Initialize sample database."""
        for i in range(1000):
            self._data_store[f"record_{i}"] = {
                "id": i,
                "data": f"sample_data_{i}",
                "values": [random.random() for _ in range(10)]
            }

    async def start(self):
        """Start the hybrid database."""
        if self._running:
            return

        self._thread_executor = ThreadPoolExecutor(
            max_workers=self.max_fast_queries,
            thread_name_prefix="db-thread"
        )
        self._process_executor = ProcessPoolExecutor(
            max_workers=self.max_analytics
        )

        self._running = True
        logger.info("Started DatabaseHybrid")

    async def stop(self):
        """Stop the hybrid database."""
        if not self._running:
            return

        self._running = False

        if self._thread_executor:
            self._thread_executor.shutdown(wait=True)
        if self._process_executor:
            self._process_executor.shutdown(wait=True)

        logger.info("Stopped DatabaseHybrid")

    async def fast_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute fast query using asyncio."""
        start_time = time.time()

        try:
            # Simulate async database query
            await asyncio.sleep(0.01)  # Network I/O simulation

            # Simple query simulation
            if query.get("type") == "get_all":
                limit = query.get("limit", 100)
                results = list(self._data_store.values())[:limit]
            elif query.get("type") == "get_by_id":
                record_id = query.get("id")
                results = [self._data_store.get(f"record_{record_id}", {})]
            else:
                results = []

            processing_time = time.time() - start_time

            with self._lock:
                self._query_metrics.append({
                    "query_type": "fast",
                    "processing_time": processing_time,
                    "result_count": len(results),
                    "success": True
                })

            return results

        except Exception as e:
            processing_time = time.time() - start_time

            with self._lock:
                self._query_metrics.append({
                    "query_type": "fast",
                    "processing_time": processing_time,
                    "result_count": 0,
                    "success": False,
                    "error": str(e)
                })

            raise

    async def cached_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute cached query using thread pool."""
        loop = asyncio.get_event_loop()
        start_time = time.time()

        try:
            results = await loop.run_in_executor(
                self._thread_executor, self._execute_cached_query, query
            )

            processing_time = time.time() - start_time

            with self._lock:
                self._query_metrics.append({
                    "query_type": "cached",
                    "processing_time": processing_time,
                    "result_count": len(results),
                    "success": True
                })

            return results

        except Exception as e:
            processing_time = time.time() - start_time

            with self._lock:
                self._query_metrics.append({
                    "query_type": "cached",
                    "processing_time": processing_time,
                    "result_count": 0,
                    "success": False,
                    "error": str(e)
                })

            raise

    async def analytics_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analytics query using process pool."""
        loop = asyncio.get_event_loop()
        start_time = time.time()

        try:
            results = await loop.run_in_executor(
                self._process_executor, self._execute_analytics_query, query
            )

            processing_time = time.time() - start_time

            with self._lock:
                self._query_metrics.append({
                    "query_type": "analytics",
                    "processing_time": processing_time,
                    "result_count": 1,  # Analytics return single result
                    "success": True
                })

            return results

        except Exception as e:
            processing_time = time.time() - start_time

            with self._lock:
                self._query_metrics.append({
                    "query_type": "analytics",
                    "processing_time": processing_time,
                    "result_count": 0,
                    "success": False,
                    "error": str(e)
                })

            raise

    def _execute_cached_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute cached query (runs in thread pool)."""
        cache_key = json.dumps(query, sort_keys=True)

        # Check cache first
        if cache_key in self._cache:
            time.sleep(0.001)  # Minimal cache access time
            return self._cache[cache_key]

        # Execute query
        if query.get("type") == "get_range":
            start_id = query.get("start_id", 0)
            end_id = query.get("end_id", 10)
            results = []
            for i in range(start_id, min(end_id, len(self._data_store))):
                results.append(self._data_store.get(f"record_{i}", {}))
        else:
            results = []

        # Cache result
        self._cache[cache_key] = results
        time.sleep(0.005)  # Simulate some processing

        return results

    def _execute_analytics_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analytics query (runs in process pool)."""
        import math

        if query.get("type") == "statistical_analysis":
            # Heavy statistical computation
            all_values = []
            for record in self._data_store.values():
                all_values.extend(record.get("values", []))

            # Compute various statistics
            mean_val = statistics.mean(all_values)
            median_val = statistics.median(all_values)
            std_dev = statistics.stdev(all_values)

            # Complex mathematical operations
            complex_result = sum(
                math.sin(x) * math.cos(x) * math.sqrt(abs(x) + 1)
                for x in all_values[:1000]  # Limit for demo
            )

            return {
                "mean": mean_val,
                "median": median_val,
                "std_dev": std_dev,
                "complex_calculation": complex_result,
                "sample_size": len(all_values)
            }
        else:
            return {"error": "Unsupported analytics query type"}

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        with self._lock:
            if not self._query_metrics:
                return {"message": "No metrics available"}

            query_types = defaultdict(list)
            for metric in self._query_metrics:
                query_types[metric["query_type"]].append(metric["processing_time"])

            stats = {}
            for qtype, times in query_types.items():
                stats[qtype] = {
                    "total_queries": len(times),
                    "avg_time": statistics.mean(times),
                    "success_rate": sum(1 for m in self._query_metrics
                                      if m["query_type"] == qtype and m["success"]) / len(times)
                }

            return {
                "query_stats": stats,
                "total_queries": len(self._query_metrics),
                "cache_size": len(self._cache),
                "data_records": len(self._data_store)
            }


# Web server route handlers
def handle_api_request(request: Request) -> Dict[str, Any]:
    """Handle API request (runs in thread/process pool based on routing)."""
    time.sleep(0.01)  # Simulate processing
    return {"message": f"Processed {request.method} {request.endpoint}", "data": request.data}

def handle_calculation_request(request: Request) -> Dict[str, Any]:
    """Handle calculation request (CPU intensive, runs in process pool)."""
    import math
    iterations = request.data.get("iterations", 10000)
    result = sum(math.sin(i) * math.cos(i) for i in range(iterations))
    return {"result": result, "iterations": iterations}

async def handle_async_request(request: Request) -> Dict[str, Any]:
    """Handle async request (I/O bound, runs in asyncio)."""
    await asyncio.sleep(0.05)  # Simulate async I/O
    return {"message": "Async processing complete", "data": request.data}


async def demonstrate_real_world_hybrids():
    """Demonstrate real-world hybrid applications."""

    print("🌐 Real-World Hybrid Applications")
    print("=" * 40)

    # 1. Web Server Hybrid
    print("\n1. Hybrid Web Server:")
    print("-" * 22)

    async with WebServerHybrid(max_threads=4, max_processes=2) as server:
        # Register routes
        @server.route("/api/data")
        def api_data_handler(request):
            return handle_api_request(request)

        @server.route("/api/calculate")
        def api_calc_handler(request):
            return handle_calculation_request(request)

        @server.route("/api/async")
        async def api_async_handler(request):
            return await handle_async_request(request)

        # Simulate requests
        requests = [
            Request("req1", "/api/data", "GET", {"param": "value1"}),
            Request("req2", "/api/calculate", "POST", {"iterations": 5000}),
            Request("req3", "/api/async", "GET", {"async": True}),
            Request("req4", "/api/data", "GET", {"param": "value2"}),
            Request("req5", "/api/calculate", "POST", {"iterations": 8000}),
        ]

        results = []
        for req in requests:
            result = await server.handle_request(req)
            results.append(result)
            print(f"  {req.request_id} -> {result.status_code} "
                  f"({result.processing_time:.3f}s, {result.worker_type})")

        server_stats = server.get_server_stats()
        print(".1f"
              f"success_rate={server_stats['success_rate']:.3f}")

    # 2. Data Pipeline Hybrid
    print("\n2. Hybrid Data Pipeline:")
    print("-" * 25)

    async with DataPipelineHybrid() as pipeline:
        # Submit test data
        submitted_ids = []
        for i in range(20):
            if i % 4 == 0:
                # Error data for testing
                data = {"error": "invalid", "values": [1, 2, 3]}
            else:
                data = {"values": [random.random() for _ in range(50)]}
            item_id = await pipeline.submit_data(data)
            submitted_ids.append(item_id)

        # Wait for processing
        await asyncio.sleep(2.0)  # Give pipeline time to process

        pipeline_stats = pipeline.get_pipeline_stats()
        print(f"Processed {pipeline_stats['total_items_processed']} items")

        if pipeline_stats['stage_stats']:
            print("Stage performance:")
            for stage, stats in pipeline_stats['stage_stats'].items():
                print(".3f"
                      f"items={stats['items_processed']}")

    # 3. Database Hybrid
    print("\n3. Hybrid Database:")
    print("-" * 19)

    async with DatabaseHybrid(max_fast_queries=5, max_analytics=1) as db:
        # Execute different types of queries
        queries = []

        # Fast queries
        for i in range(3):
            result = await db.fast_query({"type": "get_all", "limit": 10})
            queries.append(("fast", len(result)))

        # Cached queries
        for i in range(2):
            result = await db.cached_query({"type": "get_range", "start_id": 0, "end_id": 5})
            queries.append(("cached", len(result)))

        # Analytics queries
        for i in range(1):
            result = await db.analytics_query({"type": "statistical_analysis"})
            queries.append(("analytics", 1))

        print("Query results:")
        for query_type, count in queries:
            print(f"  {query_type}: {count} results")

        db_stats = db.get_database_stats()
        print("Database stats:")
        for qtype, stats in db_stats['query_stats'].items():
            print(".3f"
                  f"queries={stats['total_queries']}")

    print("\n✅ Real-world hybrid applications demonstration complete!")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Run demonstration
    asyncio.run(demonstrate_real_world_hybrids())
