"""
Advanced subprocess examples demonstrating subprocess.Popen() and process control.

This module covers:
- subprocess.Popen() for advanced process control
- Non-blocking I/O with communicate()
- Timeout handling
- Process lifecycle management
- Signal handling
- Resource management
"""

import subprocess
import time
import signal
import os
import threading
from typing import Optional, Tuple


class AdvancedSubprocessExample:
    """
    Advanced examples using subprocess.Popen() for fine-grained process control.
    """

    @staticmethod
    def basic_popen() -> None:
        """Demonstrate basic subprocess.Popen() usage."""
        print("=== Basic subprocess.Popen() Usage ===")

        print("1. Starting a process with Popen:")
        process = subprocess.Popen(['python3', '-c', 'print("Hello from Popen!"); import time; time.sleep(1)'])
        print(f"   Process PID: {process.pid}")
        print(f"   Process poll(): {process.poll()}")  # None = still running

        # Wait for completion
        print("   Waiting for process to complete...")
        return_code = process.wait()
        print(f"   Process completed with return code: {return_code}")
        print(f"   Final poll(): {process.poll()}")

    @staticmethod
    def communicate_method() -> None:
        """Demonstrate the communicate() method for I/O."""
        print("\n=== communicate() Method for I/O ===")

        print("1. Sending input and capturing output:")
        process = subprocess.Popen(
            ['python3', '-c', 'import sys; data = sys.stdin.read(); print(f"Received: {data.strip()}")'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(input="Hello from communicate!")
        print(f"   stdout: '{stdout.strip()}'")
        print(f"   stderr: '{stderr.strip()}'")
        print(f"   return code: {process.returncode}")

    @staticmethod
    def timeout_handling() -> None:
        """Demonstrate timeout handling with communicate()."""
        print("\n=== Timeout Handling ===")

        print("1. Process with timeout:")
        process = subprocess.Popen(
            ['python3', '-c', 'import time; time.sleep(5); print("Done")'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = process.communicate(timeout=2)  # 2 second timeout
            print(f"   Process completed: {stdout.strip()}")
        except subprocess.TimeoutExpired:
            print("   Process timed out after 2 seconds!")
            process.kill()  # Terminate the process
            print("   Process killed")

    @staticmethod
    def non_blocking_io() -> None:
        """Demonstrate non-blocking I/O patterns."""
        print("\n=== Non-blocking I/O Patterns ===")

        print("1. Reading output line by line:")
        process = subprocess.Popen(
            ['python3', '-c', '''
import time
for i in range(5):
    print(f"Line {i+1}")
    time.sleep(0.2)
print("Done")
            '''],
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        # Read output line by line
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"   Received: {output.strip()}")

        print(f"   Process completed with code: {process.returncode}")

    @staticmethod
    def process_groups() -> None:
        """Demonstrate process group management."""
        print("\n=== Process Groups ===")

        print("1. Creating process in new group:")
        # Create a process group so we can kill all children
        process = subprocess.Popen(
            ['python3', '-c', '''
import time
print("Child process started")
for i in range(10):
    print(f"Child: {i}")
    time.sleep(0.1)
print("Child process finished")
            '''],
            stdout=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid  # Create new process group
        )

        print(f"   Child PID: {process.pid}")
        print(f"   Process group: {os.getpgid(process.pid)}")

        # Let it run for a bit
        time.sleep(0.5)

        # Kill the entire process group
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            print("   Sent SIGTERM to process group")
        except ProcessLookupError:
            print("   Process group already terminated")

        # Wait for cleanup
        try:
            process.wait(timeout=2)
            print(f"   Process terminated with code: {process.returncode}")
        except subprocess.TimeoutExpired:
            process.kill()
            print("   Process force killed")

    @staticmethod
    def signal_handling() -> None:
        """Demonstrate signal handling with subprocess."""
        print("\n=== Signal Handling ===")

        print("1. Handling SIGTERM gracefully:")
        process = subprocess.Popen([
            'python3', '-c', '''
import signal
import time
import sys

def signal_handler(signum, frame):
    print(f"\\nReceived signal {signum}, cleaning up...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)

print("Child: Waiting for signal...")
for i in range(20):
    print(f"Child: {i}", end="\\r", flush=True)
    time.sleep(0.1)
print("\\nChild: Completed normally")
            '''
        ], stdout=subprocess.PIPE, text=True)

        # Let it run for a bit
        time.sleep(0.5)

        # Send SIGTERM
        print("   Sending SIGTERM to child process...")
        process.send_signal(signal.SIGTERM)

        # Wait for graceful termination
        try:
            stdout, _ = process.communicate(timeout=3)
            print("   Process output:")
            for line in stdout.strip().split('\\n'):
                print(f"   {line}")
        except subprocess.TimeoutExpired:
            print("   Process didn't terminate gracefully, killing...")
            process.kill()

    @staticmethod
    def resource_management() -> None:
        """Demonstrate proper resource management."""
        print("\n=== Resource Management ===")

        print("1. Using context manager pattern:")
        processes = []

        try:
            # Start multiple processes
            for i in range(3):
                process = subprocess.Popen(
                    ['python3', '-c', f'import time; time.sleep({i+1}); print("Process {i} done")'],
                    stdout=subprocess.PIPE,
                    text=True
                )
                processes.append(process)
                print(f"   Started process {i} (PID: {process.pid})")

            # Wait for all to complete
            print("   Waiting for all processes...")
            for i, process in enumerate(processes):
                stdout, _ = process.communicate()
                print(f"   Process {i} output: {stdout.strip()}")

        except Exception as e:
            print(f"   Error occurred: {e}")
            # Clean up any remaining processes
            for process in processes:
                if process.poll() is None:
                    process.kill()
        finally:
            # Ensure all processes are cleaned up
            for process in processes:
                if process.poll() is None:
                    process.wait()

    @staticmethod
    def asynchronous_processing() -> None:
        """Demonstrate asynchronous subprocess management."""
        print("\n=== Asynchronous Processing ===")

        def monitor_process(process, process_id):
            """Monitor a subprocess asynchronously."""
            try:
                stdout, stderr = process.communicate(timeout=5)
                print(f"   Process {process_id} completed:")
                if stdout:
                    print(f"   stdout: {stdout.strip()}")
                if stderr:
                    print(f"   stderr: {stderr.strip()}")
            except subprocess.TimeoutExpired:
                print(f"   Process {process_id} timed out, terminating...")
                process.kill()
            except Exception as e:
                print(f"   Process {process_id} error: {e}")

        print("1. Running multiple processes asynchronously:")
        processes = []

        # Start multiple processes
        for i in range(3):
            process = subprocess.Popen(
                ['python3', '-c', f'''
import time
import random
delay = random.uniform(0.5, 2.0)
time.sleep(delay)
print(f"Process {i} completed after {delay:.1f}s")
                '''],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            processes.append(process)

        # Start monitoring threads
        threads = []
        for i, process in enumerate(processes):
            thread = threading.Thread(target=monitor_process, args=(process, i))
            thread.start()
            threads.append(thread)

        # Wait for all monitoring threads
        for thread in threads:
            thread.join()

        print("   All processes monitored and completed")


def main() -> None:
    """Run all advanced subprocess examples."""
    print("Advanced Subprocess Examples")
    print("=" * 35)

    example = AdvancedSubprocessExample()

    try:
        example.basic_popen()
        example.communicate_method()
        example.timeout_handling()
        example.non_blocking_io()
        example.process_groups()
        example.signal_handling()
        example.resource_management()
        example.asynchronous_processing()

        print("\n" + "=" * 35)
        print("All advanced subprocess examples completed successfully!")

    except Exception as e:
        print(f"\nExample failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
