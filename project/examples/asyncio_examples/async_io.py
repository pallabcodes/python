"""
Async I/O examples demonstrating file and network operations.

This module covers:
- Async file I/O operations
- Async network operations with sockets
- HTTP client/server with aiohttp
- Stream processing
- Concurrent I/O operations
- Error handling in async I/O
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

# Optional aiohttp import
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    aiohttp = None


class AsyncIOExample:
    """
    Examples of async I/O operations.
    """

    async def async_file_read(self, file_path: str) -> str:
        """
        Read a file asynchronously.

        Args:
            file_path: Path to the file to read

        Returns:
            File contents as string
        """
        print(f"📖 Reading file: {file_path}")

        # This lock creates a temporary asynchronous lock context (like a mutex).
        async with asyncio.Lock():
            # → This is normal blocking file I/O.
            # There’s no asynchronous open in the Python standard library; the OS reads the file immediately, blocking the interpreter while it does.
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        # Simulate async behavior with small delay
        await asyncio.sleep(0.01)
        return content

    
    # this is a deceptively simple but subtle example, because it looks like it’s doing file I/O asynchronously, but under the hood it’s a mix of synchronous I/O inside an async function and simulated async behavior.
    
    async def async_file_write(self, file_path: str, content: str) -> None:
        """
        Write content to a file asynchronously.

        Args:
            file_path: Path to write to
            content: Content to write
        """
        print(f"✍️  Writing to file: {file_path}")

        # Ensure parent directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        async with asyncio.Lock():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        await asyncio.sleep(0.01)

    async def file_operations_example(self) -> None:
        """Demonstrate async file operations."""
        print("=== Async File Operations ===")

        # Creates a temporary file synchronously using tempfile.NamedTemporaryFile() named tmp.
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            # Saves its path to tmp_path.
            tmp_path = tmp.name
            # Writes a short text to it: "Hello, Async World!\nThis is a test file."
            tmp.write("Hello, Async World!\nThis is a test file.")

        try:
            # Read file's content i.e. "Hello, Async World!\nThis is a test file." asynchronously
            content = await self.async_file_read(tmp_path)
            print(f"File content: {repr(content)}")

            # Write new content
            new_content = "Modified by async operation\n" + content
            await self.async_file_write(tmp_path, new_content)

            # Read again to verify
            updated_content = await self.async_file_read(tmp_path)
            print(f"Updated content: {repr(updated_content)}")

        finally:
            # Cleanup
            os.unlink(tmp_path)

        print()

    async def concurrent_file_processing(self) -> None:
        """Demonstrate concurrent file processing."""
        print("=== Concurrent File Processing ===")

        # Create multiple test files
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'_{i}.json', delete=False) as tmp:
                data = {"id": i, "name": f"item_{i}", "value": i * 100}
                json.dump(data, tmp)
                temp_files.append(tmp.name)

        try:
            # Read all files concurrently
            read_tasks = [self.async_file_read(f) for f in temp_files]
            contents = await asyncio.gather(*read_tasks)

            print("Read contents from all files:")
            for i, content in enumerate(contents):
                data = json.loads(content)
                print(f"  File {i+1}: {data}")

            # Process and write results concurrently
            async def process_and_save(content: str, output_path: str) -> None:
                data = json.loads(content)
                data["processed"] = True
                data["timestamp"] = asyncio.get_event_loop().time()
                await self.async_file_write(output_path, json.dumps(data, indent=2))

            output_files = [f.replace('.json', '_processed.json') for f in temp_files]
            process_tasks = [
                process_and_save(content, output)
                for content, output in zip(contents, output_files)
            ]

            await asyncio.gather(*process_tasks)

            # Verify results
            verify_tasks = [self.async_file_read(f) for f in output_files]
            verify_contents = await asyncio.gather(*verify_tasks)

            print("Processed files:")
            for content in verify_contents:
                data = json.loads(content)
                print(f"  {data['name']}: processed={data['processed']}")

            # Cleanup output files
            for f in output_files:
                os.unlink(f)

        finally:
            # Cleanup input files
            for f in temp_files:
                os.unlink(f)

        print()

    async def async_network_client(self, host: str, port: int, message: str) -> str:
        """
        Simple async TCP client.

        Args:
            host: Server host
            port: Server port
            message: Message to send

        Returns:
            Server response
        """
        print(f"🌐 Connecting to {host}:{port}")

        try:
            reader, writer = await asyncio.open_connection(host, port)

            # Send message
            writer.write(message.encode())
            await writer.drain()

            # Read response upto 1024 bytes
            response = await reader.read(1024) # read() is a blocking operation that waits until the data is available
            response_str = response.decode()

            writer.close() # close the writer stream
            await writer.wait_closed()

            return response_str

        except Exception as e:
            return f"Connection failed: {e}"

    async def async_network_server(self, host: str, port: int) -> None:
        """
        Simple async TCP server.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            """Handle a client connection."""
            addr = writer.get_extra_info('peername') # gives (ip, port) of the client
            print(f"📡 New connection from {addr}")

            try:
                # Read bytes data upto 1024 bytes, ✅ Because this is await, the server coroutine pauses while waiting, allowing other clients to run.
                # So even with one thread, multiple clients can be served concurrently — cooperative multitasking.
                data = await reader.read(1024) # It suspends until some bytes arrive on the socket or the connection closes. When data arrives, it’s returned as bytes.
                message = data.decode().strip() # decode the bytes data to a string and strip any newlines and whitespaces
                print(f"📨 Received: {message}")

                # Process and respond
                response = f"Echo: {message.upper()}"
                writer.write(response.encode()) # buffers the outgoing bytes
                await writer.drain() # ensures all buffered data is actually sent over the network (flushes the buffer) and again await is non-blocking — while sending large data, the coroutine yields so others can run.

            except Exception as e:
                print(f"❌ Error handling client: {e}")
            finally:
                writer.close() # begins closing the writer stream
                await writer.wait_closed() # ensures the writer stream is fully closed and even if there's an error this method ensures writer stream closed properly.
        
        print(f"🚀 Starting server on {host}:{port}")

        server = await asyncio.start_server(handle_client, host, port)

        """
        -- async with server: ensures that when the block exits, the server is properly closed (like a context manager).
        -- await server.serve_forever() runs an infinite event loop that:
        -- Accepts new connections.
        -- Spawns handle_client tasks.
        -- Keeps serving until the server is cancelled or stopped.
        --The coroutine serve_forever() runs until externally cancelled — e.g., from another task:
        """
        async with server:
            await server.serve_forever()

    async def network_operations_example(self) -> None:
        """Demonstrate async network operations."""
        print("=== Async Network Operations ===")

        # Start server in background
        server_task = asyncio.create_task(self.async_network_server('localhost', 8888))

        # Give server time to start
        await asyncio.sleep(0.1)

        try:
            # Test client connections
            messages = ["Hello", "Async World", "Network Test"]

            client_tasks = [
                self.async_network_client('localhost', 8888, msg)
                for msg in messages
            ]

            responses = await asyncio.gather(*client_tasks)

            print("Client responses:")
            for msg, resp in zip(messages, responses):
                print(f"  '{msg}' -> '{resp.strip()}'")

        finally:
            """
            -- When it’s cancelled, the async with block ensures cleanup:
            -- closes listening sockets,
            -- stops accepting new clients,
            -- allows existing client coroutines to finish.
            """
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass

        print()

    async def async_http_client_example(self) -> None:
        """Demonstrate async HTTP client operations."""
        print("=== Async HTTP Client ===")

        if not HAS_AIOHTTP:
            print("aiohttp not available. Install with: pip install aiohttp")
            print("Skipping HTTP client example.\n")
            return

        async def fetch_url(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
            """Fetch a URL and return metadata."""
            try:
                async with session.get(url) as response:
                    content = await response.text()
                    return {
                        "url": url,
                        "status": response.status,
                        "content_length": len(content),
                        "content_type": response.headers.get('content-type', 'unknown')
                    }
            except Exception as e:
                return {"url": url, "error": str(e)}

        # Test URLs (using httpbin for reliable testing)
        urls = [
            "https://httpbin.org/get",
            "https://httpbin.org/user-agent",
            "https://httpbin.org/headers"
        ]

        async with aiohttp.ClientSession() as session:
            # Fetch all URLs concurrently
            tasks = [fetch_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            print("HTTP request results:")
            for result in results:
                if isinstance(result, Exception):
                    print(f"  ❌ Request failed: {result}")
                else:
                    url_parsed = urlparse(result["url"])
                    print(f"  ✅ {url_parsed.path}: status={result['status']}, "
                          f"size={result['content_length']}")

        print()

    async def stream_processing_example(self) -> None:
        """Demonstrate async stream processing."""
        print("=== Async Stream Processing ===")

        async def async_data_stream() -> AsyncGenerator[bytes, None]:
            """Simulate an async data stream."""
            data_chunks = [
                b"Hello, ",
                b"this is a ",
                b"streaming data ",
                b"example with ",
                b"async processing!"
            ]

            for chunk in data_chunks:
                # Simulate network delay
                await asyncio.sleep(0.1)
                yield chunk

        async def process_stream() -> str:
            """Process data from the stream."""
            result = b""
            async for chunk in async_data_stream():
                print(f"📦 Received chunk: {chunk}")
                result += chunk

                # Simulate processing time
                await asyncio.sleep(0.05)

            return result.decode()

        # Process the stream
        final_result = await process_stream()
        print(f"📄 Final processed result: {final_result}")
        print()

    async def concurrent_io_operations(self) -> None:
        """Demonstrate concurrent I/O operations."""
        print("=== Concurrent I/O Operations ===")

        async def io_operation(name: str, duration: float) -> str:
            """Simulate an I/O operation."""
            print(f"🔄 Starting I/O operation: {name}")
            await asyncio.sleep(duration)
            result = f"IO result from {name}"
            print(f"✅ Completed I/O operation: {name}")
            return result

        # Simulate different types of I/O operations
        operations = [
            ("File Read", 0.3),
            ("Network Request", 0.5),
            ("Database Query", 0.2),
            ("API Call", 0.4),
            ("Cache Lookup", 0.1)
        ]

        # get_event_loop().time() gives a high-resolution monotonic clock suitable for benchmarking.
        # It’s better than time.time() for measuring elapsed time, because it’s unaffected by system clock changes.
        start_time = asyncio.get_event_loop().time()

        # You create five coroutine objects (not yet running).
        tasks = [io_operation(name, duration) for name, duration in operations]
        # schedules all of them to run concurrently under the event loop and waits for all to finish.
        results = await asyncio.gather(*tasks)

        total_time = asyncio.get_event_loop().time() - start_time

        print("\nConcurrent I/O Results:")
        for (name, _), result in zip(operations, results):
            print(f"  {name}: {result}")

        # Calculate speedup
        sequential_time = sum(duration for _, duration in operations)
        speedup = sequential_time / total_time

        print(f"\nTotal time: {total_time:.2f}s")
        print(f"Sequential time (if done one by one): {sequential_time:.2f}s")
        print(f"Speedup: {speedup:.2f}x\n")

    async def error_handling_in_async_io(self) -> None:
        """Demonstrate error handling in async I/O operations."""
        print("=== Error Handling in Async I/O ===")

        async def unreliable_io_operation(name: str, should_fail: bool = False) -> str:
            """I/O operation that may fail."""
            await asyncio.sleep(0.1)

            if should_fail:
                if "file" in name.lower():
                    raise FileNotFoundError(f"File not found: {name}")
                elif "network" in name.lower():
                    raise ConnectionError(f"Network error: {name}")
                else:
                    raise RuntimeError(f"Unknown error in {name}")

            return f"Success: {name}"

        # Test operations with error handling
        operations = [
            ("file_operation", False),
            ("network_operation", True),
            ("database_operation", False),
            ("api_operation", True),
            ("cache_operation", False)
        ]

        print("Testing I/O operations with error handling:")
        for name, should_fail in operations:
            try:
                result = await unreliable_io_operation(name, should_fail)
                print(f"  ✅ {name}: {result}")
            except FileNotFoundError as e:
                print(f"  📁 {name}: File error - {e}")
            except ConnectionError as e:
                print(f"  🌐 {name}: Network error - {e}")
            except Exception as e:
                print(f"  ❓ {name}: Unexpected error - {e}")

        # Concurrent error handling
        print("\nTesting concurrent operations with mixed success/failure:")
        concurrent_ops = [
            unreliable_io_operation("concurrent_file", False),
            unreliable_io_operation("concurrent_network", True),
            unreliable_io_operation("concurrent_db", False),
            unreliable_io_operation("concurrent_api", True)
        ]

        # Gather with exception handling

        """
        --gather(..., return_exceptions=True) is good when you want to proceed on errors and collapse results. Otherwise gather raises on first exception.
        -- For production, consider per-task timeout with asyncio.wait_for to prevent hung ops.
        -- Classify/log exceptions properly. Good pattern.
        """
        results = await asyncio.gather(*concurrent_ops, return_exceptions=True)

        for i, result in enumerate(results):
            op_name = f"concurrent_op_{i+1}"
            if isinstance(result, Exception):
                error_type = type(result).__name__
                print(f"  ❌ {op_name}: {error_type} - {result}")
            else:
                print(f"  ✅ {op_name}: {result}")

        print()

    """
    # Caveats
      -- As before: reading/writing may be blocking if your helpers use blocking file I/O; use aiofiles or threads for real async.
      -- Cleanups: ensure try/finally covers both source and dest removal and handle missing files gracefully.
    """
    async def async_file_copy_example(self) -> None:
        """Demonstrate async file copy operations."""
        print("=== Async File Copy Operations ===")

        # Create source file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as src:
            source_path = src.name
            src.write("This is the source file content.\n")
            src.write("It has multiple lines.\n")
            src.write("And will be copied asynchronously.\n")

        dest_path = source_path.replace('.txt', '_copy.txt')

        try:
            # Async file copy
            print(f"📋 Copying {source_path} to {dest_path}")

            # Read source
            source_content = await self.async_file_read(source_path)

            # Simulate network transfer or processing
            await asyncio.sleep(0.2)

            # Write destination
            await self.async_file_write(dest_path, source_content)

            # Verify copy
            dest_content = await self.async_file_read(dest_path)

            if source_content == dest_content:
                print("✅ File copy successful!")
                print(f"Content length: {len(source_content)} characters")
            else:
                print("❌ File copy failed - content mismatch")

        finally:
            # Cleanup
            for path in [source_path, dest_path]:
                if os.path.exists(path):
                    os.unlink(path)

        print()

    """
    # Notes & caveats

        -- Uses tempfile.mktemp() — unsafe due to race conditions. Prefer tempfile.NamedTemporaryFile(delete=False) or tempfile.mkstemp() (gives open fd).

        -- batch_file_writer writes a joined JSON string — careful: splitting on \n requires exact round-trip; ensure json.dumps not producing extra newlines inside objects.

        -- Verifying expected ids is good; ensure id uniqueness across batches is correct (your expected_ids assumes ids 0..14).
    """
    async def batch_io_operations(self) -> None:
        """Demonstrate batch processing of I/O operations."""
        print("=== Batch I/O Operations ===")

        async def batch_file_writer(file_path: str, data_items: List[Dict[str, Any]]) -> str:
            """Write batch of data items to file."""
            content = "\n".join(json.dumps(item) for item in data_items)
            await self.async_file_write(file_path, content)
            return f"Wrote {len(data_items)} items to {file_path}"

        async def batch_file_reader(file_path: str) -> List[Dict[str, Any]]:
            """Read and parse batch of data items from file."""
            content = await self.async_file_read(file_path)
            items = [json.loads(line) for line in content.strip().split('\n') if line]
            return items

        # Generate batch data
        batch_data = [
            [{"id": i, "name": f"item_{i}", "batch": b} for i in range(5)]
            for b in range(3)
        ]

        temp_files = []

        try:
            # Write batches concurrently
            print("📝 Writing data batches...")
            write_tasks = []
            for i, batch in enumerate(batch_data):
                temp_file = tempfile.mktemp(suffix=f'_batch_{i}.jsonl')
                temp_files.append(temp_file)
                task = batch_file_writer(temp_file, batch)
                write_tasks.append(task)

            write_results = await asyncio.gather(*write_tasks)
            for result in write_results:
                print(f"  {result}")

            # Read and process batches concurrently
            print("\n📖 Reading and processing batches...")
            read_tasks = [batch_file_reader(f) for f in temp_files]
            read_results = await asyncio.gather(*read_tasks)

            # Process results
            total_items = sum(len(batch) for batch in read_results)
            print(f"Successfully processed {total_items} items across {len(read_results)} batches")

            # Verify data integrity
            all_items = []
            for batch in read_results:
                all_items.extend(batch)

            expected_ids = set(range(15))  # 3 batches * 5 items each
            actual_ids = set(item['id'] for item in all_items)

            if expected_ids == actual_ids:
                print("✅ Data integrity verified - all items accounted for")
            else:
                print("❌ Data integrity issue - missing or extra items")

        finally:
            # Cleanup
            for f in temp_files:
                if os.path.exists(f):
                    os.unlink(f)

        print()


async def main() -> None:
    """Run all async I/O examples."""
    print("Asyncio I/O Examples")
    print("=" * 20)

    example = AsyncIOExample()

    await example.file_operations_example()
    await example.concurrent_file_processing()
    await example.network_operations_example()
    await example.async_http_client_example()
    await example.stream_processing_example()
    await example.concurrent_io_operations()
    await example.error_handling_in_async_io()
    await example.async_file_copy_example()
    await example.batch_io_operations()

    print("All async I/O examples completed!")


if __name__ == "__main__":
    asyncio.run(main())


"""

🎯 Key Concepts Demonstrated:
File I/O with locks - Simulating async behavior for regular file operations
Concurrent file processing - Multiple files processed simultaneously
TCP networking - Async client/server with asyncio.open_connection() and start_server()
HTTP clients - Using aiohttp for concurrent web requests
Stream processing - Handling data streams with async generators
Concurrent I/O - Multiple I/O operations running simultaneously
Error handling - Specific exception types and concurrent error handling
File operations - Copying, batch processing, data integrity verification
Optional dependencies - Graceful handling when aiohttp isn't available
🔑 Why Async I/O Matters:
Scalability - Handle thousands of concurrent connections
Efficiency - Non-blocking I/O prevents thread starvation
Resource utilization - Better CPU usage for I/O-bound workloads
Real-world patterns - File processing, network clients/servers, HTTP APIs
Error resilience - Proper exception handling in concurrent operations
This file shows practical async I/O patterns that are essential for building scalable network applications and services! 🌐⚡

Common cross-cutting concerns & best practices

Blocking file I/O: open/read/write are blocking. For heavy concurrency, use aiofiles or asyncio.to_thread/run_in_executor.

Message framing for sockets: use newline or length-prefixed frames so reader.read() won't hang waiting for EOF. Use reader.readline() for line-based protocols.

Server shutdown: server_task.cancel() is okay, but the more explicit pattern is to call server.close() and await server.wait_closed() and ensure client handlers finish or are cancelled.

Temp file creation: avoid mktemp(). Use NamedTemporaryFile or mkstemp() and delete safely.

Error handling in gather:

Default gather will raise on first exception.

Use return_exceptions=True to get per-task exceptions as results and handle them.

Shared resource safety: if multiple coroutines write the same path, use asyncio.Lock() (shared instance) or per-file lock map.

Timeouts: wrap network I/O with asyncio.wait_for(...) or use client library timeouts to avoid indefinite waits.

Formatting & logging: prefer proper formatting when printing computed values (fix .2f bug).

Quick summary (one-line per function)

concurrent_file_processing: reads/processes/writes files concurrently — beware blocking file I/O.

async_network_client: simple TCP client — ensure message framing and EOF handling.

async_network_server: simple TCP server with per-client coroutine — ensure graceful shutdown.

network_operations_example: coordinates server + clients as a test harness; be careful with startup timing and cancellation.

async_http_client_example: concurrent HTTP fetches using aiohttp — good pattern; handle timeouts/errors.

stream_processing_example: stream producer + consumer via async generator — good streaming demo.

concurrent_io_operations: demonstrates concurrent I/O speedups — fix formatting bug and compute speedup correctly.

error_handling_in_async_io: shows both sequential and concurrent error handling (gather with exceptions).

async_file_copy_example: copy demo — again watch blocking I/O caveat.

batch_io_operations: batch write/read verification — replace mktemp() and ensure robust temp file handling.

"""