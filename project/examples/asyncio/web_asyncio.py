"""
Async web servers and clients using asyncio.

This module covers:
- Async HTTP server with asyncio
- Async HTTP client operations
- WebSocket communication
- REST API patterns
- Middleware and routing
- Concurrent request handling
- Error handling in web contexts
"""

import asyncio
import json
import random
import time
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

# Optional aiohttp import
try:
    import aiohttp
    from aiohttp import web
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    aiohttp = None
    web = None


class WebAsyncioExample:
    """
    Examples of async web servers and clients.
    """

    async def simple_async_http_server(self) -> None:
        """Demonstrate a simple async HTTP server."""
        print("=== Simple Async HTTP Server ===")

        if not HAS_AIOHTTP:
            print("aiohttp not available. Install with: pip install aiohttp")
            print("Skipping HTTP server example.\n")
            return

        async def hello_handler(request: web.Request) -> web.Response:
            """Simple hello handler."""
            name = request.query.get('name', 'World')
            return web.json_response({
                'message': f'Hello, {name}!',
                'timestamp': time.time(),
                'method': request.method,
                'path': request.path
            })

        async def async_work_handler(request: web.Request) -> web.Response:
            """Handler that performs async work."""
            # Simulate async I/O operation
            await asyncio.sleep(0.5)

            return web.json_response({
                'status': 'completed',
                'work_duration': 0.5,
                'server_time': time.time()
            })

        async def stats_handler(request: web.Request) -> web.Response:
            """Handler that returns server statistics."""
            return web.json_response({
                'uptime': time.time() - request.app['start_time'],
                'active_connections': random.randint(1, 10),
                'total_requests': request.app['request_count']
            })

        @web.middleware
        async def logging_middleware(request: web.Request, handler):
            """Logging middleware."""
            request.app['request_count'] += 1

            start_time = time.time()
            print(f"📨 {request.method} {request.path} - Start")

            try:
                response = await handler(request)
                duration = time.time() - start_time
                print(".2f")
                return response
            except Exception as e:
                duration = time.time() - start_time
                print(".2f")
                raise

        # Create application
        app = web.Application(middlewares=[logging_middleware])
        app['start_time'] = time.time()
        app['request_count'] = 0

        # Add routes
        app.router.add_get('/', hello_handler)
        app.router.add_get('/work', async_work_handler)
        app.router.add_get('/stats', stats_handler)

        # Start server
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()

        print("🚀 Server started on http://localhost:8080")
        print("Try these endpoints:")
        print("  GET /")
        print("  GET /?name=Alice")
        print("  GET /work")
        print("  GET /stats")
        print("Press Ctrl+C to stop")

        try:
            # Keep server running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down server...")
        finally:
            await runner.cleanup()

        print()

    async def async_http_client_operations(self) -> None:
        """Demonstrate async HTTP client operations."""
        print("=== Async HTTP Client Operations ===")

        if not HAS_AIOHTTP:
            print("aiohttp not available. Install with: pip install aiohttp")
            print("Skipping HTTP client example.\n")
            return

        async def fetch_url(session: aiohttp.ClientSession, url: str,
                          timeout: float = 5.0) -> Dict[str, Any]:
            """Fetch a URL with timeout and error handling."""
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    content = await response.text()
                    return {
                        'url': url,
                        'status': response.status,
                        'content_length': len(content),
                        'headers': dict(response.headers),
                        'success': True
                    }
            except Exception as e:
                return {
                    'url': url,
                    'error': str(e),
                    'success': False
                }

        async def concurrent_requests() -> None:
            """Make concurrent HTTP requests."""
            # Using httpbin.org for testing
            urls = [
                'https://httpbin.org/get',
                'https://httpbin.org/user-agent',
                'https://httpbin.org/headers',
                'https://httpbin.org/delay/1',  # 1 second delay
                'https://httpbin.org/delay/2',  # 2 second delay
            ]

            print(f"Fetching {len(urls)} URLs concurrently...")

            async with aiohttp.ClientSession() as session:
                # Create tasks for concurrent requests
                tasks = [fetch_url(session, url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                success_count = 0
                for result in results:
                    if isinstance(result, Exception):
                        print(f"❌ Request failed: {result}")
                    elif result.get('success'):
                        success_count += 1
                        url = result['url']
                        status = result['status']
                        size = result['content_length']
                        print(f"✅ {url}: {status} ({size} bytes)")
                    else:
                        print(f"❌ {result['url']}: {result['error']}")

                print(f"\nConcurrent requests completed: {success_count}/{len(urls)} successful")

        await concurrent_requests()
        print()

    async def simple_async_tcp_server(self) -> None:
        """Demonstrate a simple async TCP server."""
        print("=== Simple Async TCP Server ===")

        async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            """Handle a TCP client connection."""
            addr = writer.get_extra_info('peername')
            print(f"📡 New connection from {addr}")

            try:
                while True:
                    # Read data with timeout
                    try:
                        data = await asyncio.wait_for(reader.read(1024), timeout=10.0)
                    except asyncio.TimeoutError:
                        print(f"⏰ Connection timeout from {addr}")
                        break

                    if not data:
                        break

                    message = data.decode().strip()
                    print(f"📨 Received from {addr}: {message}")

                    # Process message
                    if message.upper() == 'PING':
                        response = b'PONG\n'
                    elif message.upper() == 'TIME':
                        response = f"{time.time()}\n".encode()
                    elif message.upper() == 'STATS':
                        response = f"Active connections: {len(active_connections)}\n".encode()
                    elif message.upper() == 'QUIT':
                        response = b"Goodbye!\n"
                        writer.write(response)
                        await writer.drain()
                        break
                    else:
                        response = f"Echo: {message}\n".encode()

                    writer.write(response)
                    await writer.drain()

            except Exception as e:
                print(f"❌ Error handling client {addr}: {e}")
            finally:
                print(f"🔌 Connection closed: {addr}")
                writer.close()
                await writer.wait_closed()
                active_connections.discard(writer)

        # Track active connections
        active_connections = set()

        print("🚀 Starting TCP server on localhost:8888")
        print("Try connecting with: telnet localhost 8888")
        print("Commands: PING, TIME, STATS, QUIT, or any message")
        print("Press Ctrl+C to stop")

        server = await asyncio.start_server(handle_client, 'localhost', 8888)

        try:
            async with server:
                await server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down TCP server...")
        finally:
            server.close()
            await server.wait_closed()

        print()

    async def async_websocket_server(self) -> None:
        """Demonstrate async WebSocket server."""
        print("=== Async WebSocket Server ===")

        if not HAS_AIOHTTP:
            print("aiohttp not available. Install with: pip install aiohttp")
            print("Skipping WebSocket server example.\n")
            return

        async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
            """Handle WebSocket connections."""
            ws = web.WebSocketResponse()
            await ws.prepare(request)

            print(f"🔌 WebSocket connection established: {request.remote}")

            # Send welcome message
            await ws.send_str(json.dumps({
                'type': 'welcome',
                'message': 'Connected to async WebSocket server',
                'timestamp': time.time()
            }))

            try:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                            print(f"📨 WebSocket message: {data}")

                            # Echo back with processing
                            response = {
                                'type': 'echo',
                                'original': data,
                                'processed_at': time.time(),
                                'server_info': {
                                    'uptime': time.time() - request.app['start_time'],
                                    'active_connections': len(request.app['connections'])
                                }
                            }

                            await ws.send_str(json.dumps(response))

                        except json.JSONDecodeError:
                            await ws.send_str(json.dumps({
                                'type': 'error',
                                'message': 'Invalid JSON received'
                            }))

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"❌ WebSocket error: {ws.exception()}")

                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        print("🔌 WebSocket connection closed")
                        break

            except Exception as e:
                print(f"❌ WebSocket handler error: {e}")
            finally:
                # Cleanup
                if ws in request.app['connections']:
                    request.app['connections'].remove(ws)

            return ws

        # Create WebSocket application
        app = web.Application()
        app['start_time'] = time.time()
        app['connections'] = set()

        app.router.add_get('/ws', websocket_handler)

        # Add a simple HTTP endpoint too
        async def index_handler(request: web.Request) -> web.Response:
            return web.Response(text="""
            <html>
            <head><title>Async WebSocket Server</title></head>
            <body>
                <h1>Async WebSocket Server</h1>
                <p>WebSocket endpoint: <code>ws://localhost:8081/ws</code></p>
                <script>
                    const ws = new WebSocket('ws://localhost:8081/ws');
                    ws.onmessage = function(event) {
                        console.log('Received:', event.data);
                    };
                    ws.onopen = function() {
                        ws.send(JSON.stringify({message: 'Hello from browser!'}));
                    };
                </script>
            </body>
            </html>
            """, content_type='text/html')

        app.router.add_get('/', index_handler)

        # Start server
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, 'localhost', 8081)
        await site.start()

        print("🚀 WebSocket server started on http://localhost:8081")
        print("WebSocket endpoint: ws://localhost:8081/ws")
        print("HTTP endpoint: http://localhost:8081/")
        print("Press Ctrl+C to stop")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down WebSocket server...")
        finally:
            await runner.cleanup()

        print()

    async def rest_api_pattern(self) -> None:
        """Demonstrate REST API patterns with async handling."""
        print("=== REST API Pattern ===")

        if not HAS_AIOHTTP:
            print("aiohttp not available. Install with: pip install aiohttp")
            print("Skipping REST API example.\n")
            return

        # In-memory data store
        items_db = {
            '1': {'id': '1', 'name': 'Item 1', 'value': 100},
            '2': {'id': '2', 'name': 'Item 2', 'value': 200},
        }
        next_id = 3

        async def get_items_handler(request: web.Request) -> web.Response:
            """GET /items - List all items."""
            # Simulate database delay
            await asyncio.sleep(0.1)

            limit = int(request.query.get('limit', 10))
            offset = int(request.query.get('offset', 0))

            items_list = list(items_db.values())[offset:offset + limit]

            return web.json_response({
                'items': items_list,
                'total': len(items_db),
                'limit': limit,
                'offset': offset
            })

        async def get_item_handler(request: web.Request) -> web.Response:
            """GET /items/{id} - Get single item."""
            item_id = request.match_info['id']

            await asyncio.sleep(0.05)  # Simulate database lookup

            if item_id not in items_db:
                return web.json_response({'error': 'Item not found'}, status=404)

            return web.json_response(items_db[item_id])

        async def create_item_handler(request: web.Request) -> web.Response:
            """POST /items - Create new item."""
            try:
                data = await request.json()

                # Validate required fields
                if 'name' not in data:
                    return web.json_response({'error': 'Name is required'}, status=400)

                # Simulate processing delay
                await asyncio.sleep(0.2)

                # Create new item
                nonlocal next_id
                item_id = str(next_id)
                next_id += 1

                item = {
                    'id': item_id,
                    'name': data['name'],
                    'value': data.get('value', 0),
                    'created_at': time.time()
                }

                items_db[item_id] = item

                return web.json_response(item, status=201)

            except json.JSONDecodeError:
                return web.json_response({'error': 'Invalid JSON'}, status=400)

        async def update_item_handler(request: web.Request) -> web.Response:
            """PUT /items/{id} - Update item."""
            item_id = request.match_info['id']

            if item_id not in items_db:
                return web.json_response({'error': 'Item not found'}, status=404)

            try:
                data = await request.json()

                # Simulate update delay
                await asyncio.sleep(0.15)

                # Update item
                item = items_db[item_id].copy()
                item.update(data)
                item['updated_at'] = time.time()

                items_db[item_id] = item

                return web.json_response(item)

            except json.JSONDecodeError:
                return web.json_response({'error': 'Invalid JSON'}, status=400)

        async def delete_item_handler(request: web.Request) -> web.Response:
            """DELETE /items/{id} - Delete item."""
            item_id = request.match_info['id']

            if item_id not in items_db:
                return web.json_response({'error': 'Item not found'}, status=404)

            # Simulate deletion delay
            await asyncio.sleep(0.1)

            deleted_item = items_db.pop(item_id)

            return web.json_response({
                'message': f'Item {item_id} deleted',
                'deleted_item': deleted_item
            })

        async def batch_operation_handler(request: web.Request) -> web.Response:
            """POST /batch - Perform batch operations."""
            try:
                operations = await request.json()

                results = []
                for op in operations:
                    op_type = op.get('type')
                    op_data = op.get('data', {})

                    # Simulate operation processing
                    await asyncio.sleep(0.05)

                    if op_type == 'create':
                        nonlocal next_id
                        item_id = str(next_id)
                        next_id += 1
                        item = {'id': item_id, **op_data}
                        items_db[item_id] = item
                        results.append({'operation': 'create', 'id': item_id, 'success': True})
                    elif op_type == 'update':
                        item_id = op_data.get('id')
                        if item_id in items_db:
                            items_db[item_id].update(op_data)
                            results.append({'operation': 'update', 'id': item_id, 'success': True})
                        else:
                            results.append({'operation': 'update', 'id': item_id, 'success': False, 'error': 'Not found'})
                    else:
                        results.append({'operation': op_type, 'success': False, 'error': 'Unknown operation'})

                return web.json_response({'results': results})

            except Exception as e:
                return web.json_response({'error': str(e)}, status=400)

        # Create application
        app = web.Application()

        # Add routes
        app.router.add_get('/items', get_items_handler)
        app.router.add_get('/items/{id}', get_item_handler)
        app.router.add_post('/items', create_item_handler)
        app.router.add_put('/items/{id}', update_item_handler)
        app.router.add_delete('/items/{id}', delete_item_handler)
        app.router.add_post('/batch', batch_operation_handler)

        # Start server
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, 'localhost', 8082)
        await site.start()

        print("🚀 REST API server started on http://localhost:8082")
        print("Available endpoints:")
        print("  GET    /items - List items")
        print("  GET    /items/{id} - Get item")
        print("  POST   /items - Create item")
        print("  PUT    /items/{id} - Update item")
        print("  DELETE /items/{id} - Delete item")
        print("  POST   /batch - Batch operations")
        print("Press Ctrl+C to stop")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down REST API server...")
        finally:
            await runner.cleanup()

        print()

    async def concurrent_request_simulation(self) -> None:
        """Demonstrate handling concurrent requests."""
        print("=== Concurrent Request Simulation ===")

        if not HAS_AIOHTTP:
            print("aiohttp not available. Install with: pip install aiohttp")
            print("Skipping concurrent request example.\n")
            return

        async def simulate_concurrent_clients(num_clients: int = 10) -> None:
            """Simulate multiple concurrent clients."""
            async def client_simulation(client_id: int, session: aiohttp.ClientSession) -> Dict[str, Any]:
                """Simulate a client making requests."""
                results = []

                # Make multiple requests
                for i in range(3):
                    try:
                        # Random delay to simulate think time
                        await asyncio.sleep(random.uniform(0.1, 0.5))

                        # Make request
                        async with session.get('https://httpbin.org/delay/0.1') as response:
                            results.append({
                                'request': i + 1,
                                'status': response.status,
                                'client_id': client_id
                            })

                    except Exception as e:
                        results.append({
                            'request': i + 1,
                            'error': str(e),
                            'client_id': client_id
                        })

                return {
                    'client_id': client_id,
                    'total_requests': len(results),
                    'successful_requests': len([r for r in results if 'status' in r]),
                    'results': results
                }

            print(f"Simulating {num_clients} concurrent clients...")

            async with aiohttp.ClientSession() as session:
                # Create client tasks
                client_tasks = [
                    client_simulation(client_id, session)
                    for client_id in range(1, num_clients + 1)
                ]

                # Run all clients concurrently
                start_time = time.time()
                client_results = await asyncio.gather(*client_tasks)
                total_time = time.time() - start_time

                # Analyze results
                total_requests = sum(r['total_requests'] for r in client_results)
                successful_requests = sum(r['successful_requests'] for r in client_results)

                print("\nConcurrent client simulation results:")
                print(f"  Total clients: {num_clients}")
                print(f"  Total requests: {total_requests}")
                print(f"  Successful requests: {successful_requests}")
                print(".1f")
                print(".2f")
                print(".1f")

        await simulate_concurrent_clients()
        print()


async def main() -> None:
    """Run web asyncio examples."""
    print("Asyncio Web Examples")
    print("=" * 21)

    example = WebAsyncioExample()

    # Note: These examples run servers that need to be stopped with Ctrl+C
    # For automated testing, we'll skip the server examples
    # and just show the client examples

    await example.async_http_client_operations()
    await example.concurrent_request_simulation()

    print("Web examples completed!")
    print("Note: Server examples (HTTP, TCP, WebSocket, REST API) are designed")
    print("to run interactively and be stopped with Ctrl+C. They demonstrate")
    print("full async server capabilities.")


if __name__ == "__main__":
    asyncio.run(main())
