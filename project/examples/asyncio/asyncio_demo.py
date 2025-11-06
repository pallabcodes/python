"""
Comprehensive asyncio demonstration combining multiple patterns.

This module showcases:
- Real-world async application architecture
- Concurrent data processing pipeline
- Async web API server
- Background task management
- Monitoring and metrics
- Graceful shutdown handling
- Performance benchmarking
"""

import asyncio
import json
import random
import signal
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

# Optional aiohttp import
try:
    import aiohttp
    from aiohttp import web
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    aiohttp = None
    # Create dummy classes to avoid AttributeError
    class DummyWeb:
        class Request:
            def __init__(self):
                self.app = type('App', (), {})()
                self.app.start_time = time.time()
                self.app.request_count = 0
                self.query = {}
                self.match_info = type('MatchInfo', (), {'id': '1'})()
                self.method = 'GET'
                self.path = '/'

        class Response:
            def __init__(self, text="", status=200):
                self.text = text
                self.status = status

        class Application:
            def __init__(self):
                self.router = type('Router', (), {'add_get': lambda *args: None, 'add_post': lambda *args: None})()
                self.middlewares = []

        @staticmethod
        def json_response(data, status=200):
            return DummyWeb.Response(str(data), status)

        @staticmethod
        def middleware(func):
            return func

    web = DummyWeb()


class AsyncioDemo:
    """
    Comprehensive asyncio application demonstrating real-world patterns.
    """

    def __init__(self):
        self.start_time = time.time()
        self.shutdown_event = asyncio.Event()
        self.metrics = {
            'requests_processed': 0,
            'data_items_processed': 0,
            'errors': 0,
            'active_connections': 0
        }
        self.data_store = {}
        self.background_tasks = set()

    async def initialize(self) -> None:
        """Initialize the demo application."""
        print("🚀 Initializing Asyncio Demo Application...")

        # Initialize data store with sample data
        for i in range(100):
            self.data_store[str(i)] = {
                'id': str(i),
                'name': f'Item {i}',
                'value': random.randint(1, 1000),
                'category': random.choice(['A', 'B', 'C', 'D']),
                'created_at': time.time() - random.uniform(0, 86400)  # Random time in last 24h
            }

        print(f"✅ Initialized with {len(self.data_store)} data items")

        # Start background monitoring task
        monitoring_task = asyncio.create_task(self.monitoring_loop())
        self.background_tasks.add(monitoring_task)
        monitoring_task.add_done_callback(self.background_tasks.discard)

        # Start data processing pipeline
        pipeline_task = asyncio.create_task(self.data_processing_pipeline())
        self.background_tasks.add(pipeline_task)
        pipeline_task.add_done_callback(self.background_tasks.discard)

        print("✅ Background tasks started")

    async def monitoring_loop(self) -> None:
        """Background monitoring and metrics collection."""
        print("📊 Starting monitoring loop...")

        while not self.shutdown_event.is_set():
            try:
                # Collect metrics
                self.metrics['uptime'] = time.time() - self.start_time
                self.metrics['memory_items'] = len(self.data_store)

                # Print status every 5 seconds
                if int(time.time()) % 5 == 0:
                    print(f"📈 Status: {self.metrics['requests_processed']} req, "
                          f"{self.metrics['data_items_processed']} items, "
                          ".1f")

                await asyncio.sleep(1)

            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                await asyncio.sleep(1)

        print("🛑 Monitoring loop stopped")

    async def data_processing_pipeline(self) -> None:
        """Continuous data processing pipeline."""
        print("🔄 Starting data processing pipeline...")

        while not self.shutdown_event.is_set():
            try:
                # Simulate data arrival
                await asyncio.sleep(random.uniform(0.5, 2.0))

                # Generate new data item
                item_id = str(len(self.data_store))
                item = {
                    'id': item_id,
                    'name': f'Generated Item {item_id}',
                    'value': random.randint(1, 1000),
                    'category': random.choice(['A', 'B', 'C', 'D']),
                    'created_at': time.time(),
                    'processed': False
                }

                # Process the item through pipeline stages
                processed_item = await self.process_data_item(item)

                # Store processed item
                self.data_store[item_id] = processed_item
                self.metrics['data_items_processed'] += 1

            except Exception as e:
                print(f"❌ Pipeline error: {e}")
                self.metrics['errors'] += 1
                await asyncio.sleep(1)

        print("🛑 Data processing pipeline stopped")

    async def process_data_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a data item through multiple pipeline stages."""

        # Stage 1: Validation
        await asyncio.sleep(0.01)  # Simulate validation time
        if not item.get('name'):
            item['name'] = f'Item {item["id"]}'

        # Stage 2: Enrichment
        await asyncio.sleep(0.02)  # Simulate enrichment time
        item['enriched_value'] = item['value'] * 1.1
        item['category_info'] = f"Category {item['category']} group"

        # Stage 3: Quality check
        await asyncio.sleep(0.01)  # Simulate quality check
        item['quality_score'] = random.uniform(0.7, 1.0)
        item['processed'] = True
        item['processed_at'] = time.time()

        return item

    async def api_handler_get_items(self, request: web.Request) -> web.Response:
        """GET /api/items - Retrieve items with filtering."""
        try:
            # Parse query parameters
            limit = min(int(request.query.get('limit', 10)), 100)
            offset = int(request.query.get('offset', 0))
            category = request.query.get('category')

            # Filter items
            items = list(self.data_store.values())

            if category:
                items = [item for item in items if item.get('category') == category]

            # Apply pagination
            total = len(items)
            items = items[offset:offset + limit]

            # Simulate database query time
            await asyncio.sleep(0.01)

            self.metrics['requests_processed'] += 1

            return web.json_response({
                'items': items,
                'total': total,
                'limit': limit,
                'offset': offset,
                'category_filter': category
            })

        except Exception as e:
            self.metrics['errors'] += 1
            return web.json_response({'error': str(e)}, status=500)

    async def api_handler_get_item(self, request: web.Request) -> web.Response:
        """GET /api/items/{id} - Retrieve single item."""
        try:
            item_id = request.match_info['id']

            # Simulate database lookup
            await asyncio.sleep(0.005)

            if item_id not in self.data_store:
                return web.json_response({'error': 'Item not found'}, status=404)

            item = self.data_store[item_id]
            self.metrics['requests_processed'] += 1

            return web.json_response(item)

        except Exception as e:
            self.metrics['errors'] += 1
            return web.json_response({'error': str(e)}, status=500)

    async def api_handler_create_item(self, request: web.Request) -> web.Response:
        """POST /api/items - Create new item."""
        try:
            data = await request.json()

            # Validate required fields
            if 'name' not in data:
                return web.json_response({'error': 'Name is required'}, status=400)

            # Simulate processing time
            await asyncio.sleep(0.02)

            # Create new item
            item_id = str(len(self.data_store))
            item = {
                'id': item_id,
                'name': data['name'],
                'value': data.get('value', random.randint(1, 1000)),
                'category': data.get('category', random.choice(['A', 'B', 'C', 'D'])),
                'created_at': time.time(),
                'processed': False
            }

            # Process the item
            processed_item = await self.process_data_item(item)
            self.data_store[item_id] = processed_item

            self.metrics['requests_processed'] += 1
            self.metrics['data_items_processed'] += 1

            return web.json_response(processed_item, status=201)

        except json.JSONDecodeError:
            return web.json_response({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            self.metrics['errors'] += 1
            return web.json_response({'error': str(e)}, status=500)

    async def api_handler_stats(self, request: web.Request) -> web.Response:
        """GET /api/stats - Get application statistics."""
        try:
            await asyncio.sleep(0.005)  # Simulate stats collection

            # Calculate additional metrics
            category_counts = defaultdict(int)
            for item in self.data_store.values():
                category_counts[item.get('category', 'unknown')] += 1

            stats = {
                **self.metrics,
                'total_items': len(self.data_store),
                'category_breakdown': dict(category_counts),
                'server_info': {
                    'uptime': time.time() - self.start_time,
                    'python_version': f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
                }
            }

            self.metrics['requests_processed'] += 1
            return web.json_response(stats)

        except Exception as e:
            self.metrics['errors'] += 1
            return web.json_response({'error': str(e)}, status=500)

    async def api_handler_batch_process(self, request: web.Request) -> web.Response:
        """POST /api/batch - Process multiple items concurrently."""
        try:
            batch_data = await request.json()

            if not isinstance(batch_data, list):
                return web.json_response({'error': 'Expected list of items'}, status=400)

            if len(batch_data) > 50:
                return web.json_response({'error': 'Batch too large (max 50)'}, status=400)

            # Process items concurrently
            async def process_batch_item(item_data: Dict[str, Any]) -> Dict[str, Any]:
                # Create item from data
                item_id = f"batch_{random.randint(10000, 99999)}"
                item = {
                    'id': item_id,
                    'name': item_data.get('name', f'Batch Item {item_id}'),
                    'value': item_data.get('value', random.randint(1, 1000)),
                    'category': item_data.get('category', random.choice(['A', 'B', 'C', 'D'])),
                    'created_at': time.time(),
                    'processed': False
                }

                # Process through pipeline
                processed_item = await self.process_data_item(item)
                self.data_store[item_id] = processed_item
                return processed_item

            # Process all items concurrently
            tasks = [process_batch_item(item_data) for item_data in batch_data]
            processed_items = await asyncio.gather(*tasks)

            self.metrics['requests_processed'] += 1
            self.metrics['data_items_processed'] += len(processed_items)

            return web.json_response({
                'processed_items': processed_items,
                'count': len(processed_items)
            })

        except json.JSONDecodeError:
            return web.json_response({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            self.metrics['errors'] += 1
            return web.json_response({'error': str(e)}, status=500)

    @web.middleware
    async def logging_middleware(self, request: web.Request, handler):
        """Request logging middleware."""
        start_time = time.time()

        # Track active connections
        self.metrics['active_connections'] += 1

        try:
            response = await handler(request)
            duration = time.time() - start_time

            print(f"📨 {request.method} {request.path} -> {response.status} "
                  ".3f")

            return response

        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ {request.method} {request.path} -> ERROR "
                  ".3f")
            raise
        finally:
            self.metrics['active_connections'] -= 1

    async def create_web_app(self) -> web.Application:
        """Create the web application."""
        app = web.Application(middlewares=[self.logging_middleware])

        # Store reference to demo instance
        app['demo'] = self

        # Add routes
        app.router.add_get('/api/items', self.api_handler_get_items)
        app.router.add_get('/api/items/{id}', self.api_handler_get_item)
        app.router.add_post('/api/items', self.api_handler_create_item)
        app.router.add_get('/api/stats', self.api_handler_stats)
        app.router.add_post('/api/batch', self.api_handler_batch_process)

        # Add root endpoint
        async def root_handler(request: web.Request) -> web.Response:
            return web.json_response({
                'message': 'Asyncio Demo API',
                'version': '1.0.0',
                'endpoints': {
                    'GET /api/items': 'List items with optional filtering',
                    'GET /api/items/{id}': 'Get single item',
                    'POST /api/items': 'Create new item',
                    'GET /api/stats': 'Get application statistics',
                    'POST /api/batch': 'Process multiple items concurrently'
                },
                'uptime': time.time() - self.start_time
            })

        app.router.add_get('/', root_handler)

        return app

    async def graceful_shutdown(self) -> None:
        """Perform graceful shutdown."""
        print("🛑 Initiating graceful shutdown...")

        # Signal shutdown to background tasks
        self.shutdown_event.set()

        # Wait for background tasks to complete (with timeout)
        if self.background_tasks:
            print(f"Waiting for {len(self.background_tasks)} background tasks to complete...")
            done, pending = await asyncio.wait(
                self.background_tasks,
                timeout=5.0,
                return_when=asyncio.ALL_COMPLETED
            )

            if pending:
                print(f"⚠️  {len(pending)} tasks did not complete within timeout, cancelling...")
                for task in pending:
                    task.cancel()

                # Wait a bit more for cancellation
                await asyncio.wait(pending, timeout=2.0)

        print("✅ Graceful shutdown completed")

    async def run_demo(self) -> None:
        """Run the complete asyncio demo."""
        print("🎯 Starting Comprehensive Asyncio Demo")
        print("=" * 50)

        if not HAS_AIOHTTP:
            print("❌ aiohttp not available. Install with: pip install aiohttp")
            print("Cannot run web server demo.")
            return

        # Initialize application
        await self.initialize()

        # Create web application
        app = await self.create_web_app()

        # Start web server
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()

        print("🚀 Demo application started!")
        print("🌐 Web API available at: http://localhost:8080")
        print("📖 API Documentation: http://localhost:8080/")
        print("📊 Statistics: http://localhost:8080/api/stats")
        print("Press Ctrl+C to stop")

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            print(f"\n📡 Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.graceful_shutdown())

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler, sig, None)

        try:
            # Keep the application running
            while not self.shutdown_event.is_set():
                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received")
            await self.graceful_shutdown()

        finally:
            print("🧹 Cleaning up...")
            await runner.cleanup()
            print("🏁 Demo completed!")


async def benchmark_asyncio_performance() -> None:
    """Benchmark asyncio performance vs sequential execution."""
    print("🧪 Asyncio Performance Benchmark")
    print("=" * 35)

    async def cpu_bound_task(n: int) -> int:
        """CPU-bound task for benchmarking."""
        result = 0
        for i in range(n):
            result += i ** 2
        return result

    async def io_bound_task(delay: float) -> float:
        """I/O-bound task for benchmarking."""
        await asyncio.sleep(delay)
        return delay

    # Benchmark parameters
    cpu_iterations = 50000
    io_delay = 0.01
    num_tasks = 20

    print(f"Benchmarking with {num_tasks} tasks...")

    # CPU-bound benchmark
    print("\n🔢 CPU-bound tasks:")

    # Sequential
    start_time = time.time()
    sequential_results = []
    for i in range(num_tasks):
        result = await cpu_bound_task(cpu_iterations // num_tasks)
        sequential_results.append(result)
    sequential_time = time.time() - start_time

    print(".2f")

    # Concurrent
    start_time = time.time()
    concurrent_results = await asyncio.gather(*[
        cpu_bound_task(cpu_iterations // num_tasks)
        for _ in range(num_tasks)
    ])
    concurrent_time = time.time() - start_time

    print(".2f")
    if concurrent_time > 0:
        print(".2f")

    # I/O-bound benchmark
    print("\n📡 I/O-bound tasks:")

    # Sequential
    start_time = time.time()
    sequential_io_results = []
    for i in range(num_tasks):
        result = await io_bound_task(io_delay)
        sequential_io_results.append(result)
    sequential_io_time = time.time() - start_time

    print(".2f")

    # Concurrent
    start_time = time.time()
    concurrent_io_results = await asyncio.gather(*[
        io_bound_task(io_delay)
        for _ in range(num_tasks)
    ])
    concurrent_io_time = time.time() - start_time

    print(".2f")
    if concurrent_io_time > 0:
        print(".2f")

    print("\n💡 Key insights:")
    print("  - CPU-bound tasks: Limited benefit from asyncio (GIL)")
    print("  - I/O-bound tasks: Significant speedup with concurrency")
    print("  - Asyncio excels at I/O concurrency, not CPU parallelism")
    print()


async def main() -> None:
    """Main entry point for the asyncio demo."""
    print("Asyncio Comprehensive Demo")
    print("=" * 30)

    # Run performance benchmark first
    await benchmark_asyncio_performance()

    # Run the full demo application
    demo = AsyncioDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
