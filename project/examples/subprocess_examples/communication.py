"""
Subprocess communication examples demonstrating various IPC methods.

This module covers:
- Pipe-based communication
- Streaming I/O
- JSON communication protocols
- Binary data transfer
- Multi-process pipelines
- Asynchronous communication patterns
"""

import subprocess
import json
import pickle
import time
import threading
from typing import Any, Dict, List


class SubprocessCommunicationExample:
    """
    Examples of various communication patterns with subprocesses.

    When to Use:
        - Inter-process communication
        - Data exchange with subprocesses
        - Streaming data processing
        - Protocol-based communication
        - Multi-process pipelines

    Real-World Examples:
        - Data pipelines: Pass data between processes
        - Command-line tools: Communicate with CLI tools
        - Data processing: Stream data to processors
        - Protocol handlers: JSON/XML protocols
        - Binary data: Transfer binary data

    Gotchas:
        - Buffer size limits
        - Deadlock with bidirectional pipes
        - Encoding issues with text
        - Process cleanup required
        - Blocking I/O operations

    Performance Notes:
        - Pipe overhead for IPC
        - Buffer size affects performance
        - Streaming reduces memory usage
        - Binary more efficient than text
    """

    @staticmethod
    def pipe_communication() -> None:
        """Demonstrate basic pipe-based communication."""
        print("=== Pipe-based Communication ===")

        print("1. Sending data through stdin:")
        # Create a process that reads from stdin and processes it
        process = subprocess.Popen(
            ['python3', '-c', '''
import sys
data = sys.stdin.read()
words = data.strip().split()
print(f"Received {len(words)} words: {words[:3]}{'...' if len(words) > 3 else ''}")
print(f"Total characters: {len(data)}")
            '''],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send data to stdin
        input_data = "Hello World from Python subprocess communication example!"
        stdout, stderr = process.communicate(input=input_data)

        print(f"   Input sent: '{input_data}'")
        print(f"   Process output: {stdout.strip()}")
        print(f"   Return code: {process.returncode}")

    @staticmethod
    def json_protocol() -> None:
        """Demonstrate JSON-based communication protocol."""
        print("\n=== JSON Communication Protocol ===")

        print("1. JSON request-response pattern:")
        # Process that handles JSON commands
        process = subprocess.Popen(
            ['python3', '-c', '''
import sys
import json

def handle_command(cmd):
    if cmd["action"] == "add":
        return {"result": cmd["a"] + cmd["b"]}
    elif cmd["action"] == "multiply":
        return {"result": cmd["a"] * cmd["b"]}
    elif cmd["action"] == "echo":
        return {"echoed": cmd["message"]}
    else:
        return {"error": "Unknown action"}

# Read JSON from stdin
try:
    data = sys.stdin.read()
    command = json.loads(data)
    response = handle_command(command)
    print(json.dumps(response))
except Exception as e:
    print(json.dumps({"error": str(e)}))
            '''],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send JSON commands
        commands = [
            {"action": "add", "a": 10, "b": 20},
            {"action": "multiply", "a": 5, "b": 8},
            {"action": "echo", "message": "Hello JSON!"}
        ]

        for cmd in commands:
            # Start a new process for each command (could reuse in real implementation)
            proc = subprocess.Popen(
                ['python3', '-c', '''
import sys
import json

def handle_command(cmd):
    if cmd["action"] == "add":
        return {"result": cmd["a"] + cmd["b"]}
    elif cmd["action"] == "multiply":
        return {"result": cmd["a"] * cmd["b"]}
    elif cmd["action"] == "echo":
        return {"message": cmd["message"], "timestamp": "processed"}
    else:
        return {"error": "Unknown action"}

try:
    data = sys.stdin.read()
    command = json.loads(data)
    response = handle_command(command)
    print(json.dumps(response))
except Exception as e:
    print(json.dumps({"error": str(e)}))
                '''],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = proc.communicate(input=json.dumps(cmd))
            response = json.loads(stdout.strip())
            print(f"   Command: {cmd}")
            print(f"   Response: {response}")

    @staticmethod
    def binary_communication() -> None:
        """Demonstrate binary data communication."""
        print("\n=== Binary Data Communication ===")

        print("1. Sending binary data:")
        # Process that handles binary data
        process = subprocess.Popen(
            ['python3', '-c', '''
import sys
import struct

# Read binary data (4 floats)
data = sys.stdin.buffer.read(16)  # 4 * 4 bytes
floats = struct.unpack('4f', data)

print(f"Received 4 floats: {floats}")
print(f"Sum: {sum(floats)}")
print(f"Average: {sum(floats)/len(floats)}")
            '''],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Send binary float data
        import struct
        floats = [3.14, 2.71, 1.41, 1.73]
        binary_data = struct.pack('4f', *floats)

        stdout, stderr = process.communicate(input=binary_data)

        print(f"   Sent floats: {floats}")
        print(f"   Process output: {stdout.decode().strip()}")

    @staticmethod
    def streaming_communication() -> None:
        """Demonstrate streaming communication patterns."""
        print("\n=== Streaming Communication ===")

        print("1. Line-based streaming:")
        process = subprocess.Popen(
            ['python3', '-c', '''
import sys
import time

print("Stream processor started")
count = 0

for line in sys.stdin:
    line = line.strip()
    if line == "END":
        break
    count += 1
    print(f"Processed line {count}: {line.upper()}")
    time.sleep(0.1)  # Simulate processing time

print(f"Total lines processed: {count}")
            '''],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )

        # Send data line by line
        lines = ["hello", "world", "python", "subprocess", "streaming"]
        input_data = "\n".join(lines) + "\nEND\n"

        stdout, stderr = process.communicate(input=input_data)

        print("   Input lines sent:")
        for line in lines:
            print(f"   - {line}")
        print("   Process output:")
        for line in stdout.strip().split('\n'):
            print(f"   {line}")

    @staticmethod
    def multi_process_pipeline() -> None:
        """Demonstrate multi-process pipeline communication."""
        print("\n=== Multi-Process Pipeline ===")

        print("1. Text processing pipeline:")
        # Process 1: Generate text
        p1 = subprocess.Popen(
            ['python3', '-c', '''
for i in range(5):
    print(f"Line {i+1}: This is sample text {i+1}")
            '''],
            stdout=subprocess.PIPE,
            text=True
        )

        # Process 2: Filter lines
        p2 = subprocess.Popen(
            ['grep', 'Line [13]'],  # Only lines 1 and 3
            stdin=p1.stdout,
            stdout=subprocess.PIPE,
            text=True
        )
        p1.stdout.close()  # Allow p1 to receive SIGPIPE

        # Process 3: Count words
        p3 = subprocess.Popen(
            ['python3', '-c', '''
import sys
count = 0
for line in sys.stdin:
    words = line.strip().split()
    count += len(words)
    print(f"Counted {len(words)} words in: {line.strip()}")
print(f"Total words: {count}")
            '''],
            stdin=p2.stdout,
            stdout=subprocess.PIPE,
            text=True
        )
        p2.stdout.close()

        # Get final output
        stdout, stderr = p3.communicate()
        print("   Pipeline output:")
        for line in stdout.strip().split('\n'):
            print(f"   {line}")

    @staticmethod
    def asynchronous_communication() -> None:
        """Demonstrate asynchronous communication patterns."""
        print("\n=== Asynchronous Communication ===")

        def run_command_async(cmd: List[str], input_data: str = None) -> subprocess.Popen:
            """Run a command asynchronously."""
            return subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE if input_data else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

        def monitor_process(process: subprocess.Popen, name: str):
            """Monitor a process asynchronously."""
            try:
                stdout, stderr = process.communicate(timeout=5)
                print(f"   {name} completed:")
                if stdout:
                    for line in stdout.strip().split('\n'):
                        print(f"   {name}: {line}")
            except subprocess.TimeoutExpired:
                print(f"   {name} timed out, terminating...")
                process.kill()
                process.wait()  # Wait for cleanup to prevent zombie process

        print("1. Running multiple commands asynchronously:")
        commands = [
            (['python3', '-c', 'import time; time.sleep(0.5); print("Fast task done")'], "fast"),
            (['python3', '-c', 'import time; time.sleep(1.0); print("Medium task done")'], "medium"),
            (['python3', '-c', 'import time; time.sleep(1.5); print("Slow task done")'], "slow")
        ]

        processes = []
        for cmd, name in commands:
            process = run_command_async(cmd)
            processes.append((process, name))

        # Start monitoring threads
        threads = []
        for process, name in processes:
            thread = threading.Thread(target=monitor_process, args=(process, name))
            thread.start()
            threads.append(thread)

        # Wait for all monitoring threads
        for thread in threads:
            thread.join()

        print("   All asynchronous commands completed")

    @staticmethod
    def error_protocols() -> None:
        """Demonstrate error handling and protocols."""
        print("\n=== Error Handling Protocols ===")

        print("1. Structured error responses:")
        process = subprocess.Popen(
            ['python3', '-c', '''
import sys
import json

def process_request(request):
    try:
        if request["action"] == "divide":
            if request["b"] == 0:
                return {"error": "Division by zero", "code": "DIVISION_ERROR"}
            return {"result": request["a"] / request["b"]}
        elif request["action"] == "invalid":
            raise ValueError("Invalid action requested")
        else:
            return {"error": "Unknown action", "code": "UNKNOWN_ACTION"}
    except Exception as e:
        return {"error": str(e), "code": "PROCESSING_ERROR"}

# Process multiple requests
for line in sys.stdin:
    try:
        request = json.loads(line.strip())
        response = process_request(request)
        print(json.dumps(response))
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON", "code": "PARSE_ERROR"}))
            '''],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send various requests
        requests = [
            {"action": "divide", "a": 10, "b": 2},
            {"action": "divide", "a": 10, "b": 0},
            {"action": "invalid"},
            {"action": "unknown"}
        ]

        input_data = "\n".join(json.dumps(req) for req in requests) + "\n"
        stdout, stderr = process.communicate(input=input_data)

        print("   Request-Response protocol:")
        responses = stdout.strip().split('\n')
        for req, resp in zip(requests, responses):
            response_data = json.loads(resp)
            print(f"   {req} → {response_data}")

    def communication_real_world_example(self) -> None:
        """
        Real-World Scenario: Subprocess Communication - Data Processing Pipeline.

        REAL-WORLD SCENARIO:
        ====================
        You're building a data processing pipeline:
        - Process data through multiple stages
        - Each stage is a separate process
        - Problem: Need to pass data between processes
        
        THE PROBLEM WITHOUT COMMUNICATION:
        ====================================
        - No IPC → can't pass data between processes
        - File-based → slow and complex
        - No streaming → memory issues
        - No protocol → error-prone
        - System inefficient → poor performance
        
        THE SOLUTION:
        =============
        Subprocess communication enables:
        - Pipe-based IPC → efficient data transfer
        - Streaming data → low memory usage
        - Protocol-based → reliable communication
        - Process pipelines → scalable architecture
        - Efficient data flow → optimal performance
        
        WHEN TO USE SUBPROCESS COMMUNICATION:
        ====================================
        ✅ Data processing pipelines
        ✅ Multi-stage processing
        ✅ Streaming data processing
        ✅ Process coordination
        ✅ Data transformation pipelines
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Data Processing Pipeline")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Data processing pipeline")
        print("  - Process data through multiple stages")
        print("  - Each stage is a separate process")
        print("  - Problem: Need to pass data between processes")
        print()
        print("THE PROBLEM:")
        print("  Without communication:")
        print("    ❌ No IPC → can't pass data between processes")
        print("    ❌ File-based → slow and complex")
        print("    ❌ No streaming → memory issues")
        print("    ❌ No protocol → error-prone")
        print()
        print("THE SOLUTION:")
        print("  With subprocess communication:")
        print("    ✅ Pipe-based IPC → efficient data transfer")
        print("    ✅ Streaming data → low memory usage")
        print("    ✅ Protocol-based → reliable communication")
        print("    ✅ Process pipelines → scalable architecture")
        print()
        print("=" * 70)
        print()

        # Simulate a data processing pipeline
        print("Simulating data processing pipeline...")
        print("  Stage 1: Generate data")
        print("  Stage 2: Process data")
        print("  Stage 3: Aggregate results")
        print()

        # Stage 1: Generate data (Python script)
        stage1_code = """
import json
import sys
for i in range(5):
    data = {"id": i+1, "value": (i+1) * 10}
    print(json.dumps(data))
    sys.stdout.flush()
"""

        # Stage 2: Process data (Python script)
        stage2_code = """
import json
import sys
for line in sys.stdin:
    data = json.loads(line.strip())
    data["processed"] = True
    data["result"] = data["value"] * 2
    print(json.dumps(data))
    sys.stdout.flush()
"""

        try:
            # Create pipeline: stage1 | stage2
            stage1 = subprocess.Popen(
                ["python3", "-c", stage1_code],
                stdout=subprocess.PIPE,
                text=True
            )
            
            stage2 = subprocess.Popen(
                ["python3", "-c", stage2_code],
                stdin=stage1.stdout,
                stdout=subprocess.PIPE,
                text=True
            )
            
            stage1.stdout.close()  # Allow stage1 to receive SIGPIPE if stage2 exits
            
            # Collect results
            results = []
            for line in stage2.stdout:
                data = json.loads(line.strip())
                results.append(data)
                print(f"  Processed: {data}")

            stage2.wait()
            stage1.wait()

            print()
            print(f"Results: {len(results)} items processed")
            print("  ✅ Subprocess communication enabled pipeline processing!")
        except Exception as e:
            print(f"  ❌ Pipeline failed: {e}")

        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE SUBPROCESS COMMUNICATION:")
        print("   ✅ Data processing pipelines")
        print("   ✅ Multi-stage processing")
        print("   ✅ Streaming data processing")
        print("   ✅ Process coordination")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Efficient IPC")
        print("   - Streaming data processing")
        print("   - Protocol-based communication")
        print("   - Scalable pipelines")
        print("=" * 70)
        print()


def main() -> None:
    """Run all communication examples."""
    print("Subprocess Communication Examples")
    print("=" * 40)

    example = SubprocessCommunicationExample()

    try:
        example.pipe_communication()
        example.json_protocol()
        example.binary_communication()
        example.streaming_communication()
        example.multi_process_pipeline()
        example.asynchronous_communication()
        example.error_protocols()

        # Real-world scenarios
        print("\n" + "=" * 70)
        print("RUNNING REAL-WORLD SCENARIOS")
        print("=" * 70 + "\n")
        example.communication_real_world_example()

        print("\n" + "=" * 40)
        print("All communication examples completed successfully!")

    except Exception as e:
        print(f"\nExample failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
