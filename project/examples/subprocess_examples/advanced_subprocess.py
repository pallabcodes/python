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
import sys
import time
import signal
import os
import threading
from typing import Optional, Tuple


class AdvancedSubprocessExample:
    """
    Advanced examples using subprocess.Popen() for fine-grained process control.

    When to Use:
        - Non-blocking process execution
        - Process lifecycle management
        - Signal handling
        - Timeout management
        - Advanced I/O control

    Real-World Examples:
        - Long-running processes: Manage lifecycle
        - Process monitoring: Monitor process state
        - Signal handling: Handle termination signals
        - Timeout management: Kill hung processes
        - Interactive processes: Handle I/O interactively

    Gotchas:
        - Must call wait() or communicate()
        - Zombie processes if not waited
        - Signal handling platform-specific
        - Process groups for cleanup
        - Resource cleanup required

    Performance Notes:
        - Non-blocking execution
        - Process overhead significant
        - Use process pools for many processes
        - Balance timeout vs responsiveness
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
            process.wait()  # Wait for cleanup to prevent zombie process
            print("   Process killed and cleaned up")

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
            process.wait()  # Wait for cleanup to prevent zombie process
            print("   Process force killed and cleaned up")

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
            process.wait()  # Wait for cleanup to prevent zombie process

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
                    process.wait()  # Wait for cleanup to prevent zombie process
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
                process.wait()  # Wait for cleanup to prevent zombie process
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

    def advanced_subprocess_real_world_example(self) -> None:
        """
        Real-World Scenario: Advanced Subprocess - Long-Running Process Manager.

        REAL-WORLD SCENARIO:
        ====================
        You're building a process manager:
        - Start long-running background processes
        - Monitor process health
        - Handle timeouts and failures
        - Problem: Need fine-grained process control
        
        THE PROBLEM WITHOUT ADVANCED SUBPROCESS:
        ========================================
        - subprocess.run() blocks → can't monitor
        - No process control → can't manage lifecycle
        - No timeout handling → hung processes
        - No signal handling → can't terminate gracefully
        - System resource leaks → processes accumulate
        
        THE SOLUTION:
        =============
        Advanced subprocess (Popen) enables:
        - Non-blocking execution → monitor processes
        - Process lifecycle management → control processes
        - Timeout handling → kill hung processes
        - Signal handling → graceful termination
        - Resource management → prevent leaks
        
        WHEN TO USE ADVANCED SUBPROCESS:
        =================================
        ✅ Long-running process management
        ✅ Process monitoring systems
        ✅ Timeout handling
        ✅ Signal handling
        ✅ Resource management
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Long-Running Process Manager")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Process manager for long-running processes")
        print("  - Start background processes")
        print("  - Monitor process health")
        print("  - Handle timeouts and failures")
        print("  - Problem: Need fine-grained process control")
        print()
        print("THE PROBLEM:")
        print("  Without advanced subprocess:")
        print("    ❌ subprocess.run() blocks → can't monitor")
        print("    ❌ No process control → can't manage lifecycle")
        print("    ❌ No timeout handling → hung processes")
        print("    ❌ No signal handling → can't terminate gracefully")
        print()
        print("THE SOLUTION:")
        print("  With advanced subprocess (Popen):")
        print("    ✅ Non-blocking execution → monitor processes")
        print("    ✅ Process lifecycle management → control processes")
        print("    ✅ Timeout handling → kill hung processes")
        print("    ✅ Signal handling → graceful termination")
        print()
        print("=" * 70)
        print()

        def monitor_process(process: subprocess.Popen, process_id: int) -> None:
            """Monitor a process and handle timeouts."""
            try:
                stdout, stderr = process.communicate(timeout=2.0)
                if process.returncode == 0:
                    print(f"  Process {process_id}: Completed successfully")
                else:
                    print(f"  Process {process_id}: Failed with code {process.returncode}")
            except subprocess.TimeoutExpired:
                print(f"  Process {process_id}: Timeout - terminating")
                process.kill()
                process.wait()
                print(f"  Process {process_id}: Terminated")

        print("Starting and monitoring processes...")
        print()

        processes = []
        for i in range(3):
            # Start a process (simulate with sleep)
            process = subprocess.Popen(
                ["sleep", "1"] if sys.platform != "win32" else ["timeout", "/t", "1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            processes.append((process, i+1))
            print(f"  Started process {i+1} (PID: {process.pid})")

        # Monitor processes
        threads = []
        for process, process_id in processes:
            thread = threading.Thread(target=monitor_process, args=(process, process_id))
            thread.start()
            threads.append(thread)

        # Wait for monitoring threads
        for thread in threads:
            thread.join()

        print()
        print("  ✅ Advanced subprocess enabled process management!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE ADVANCED SUBPROCESS:")
        print("   ✅ Long-running process management")
        print("   ✅ Process monitoring systems")
        print("   ✅ Timeout handling")
        print("   ✅ Signal handling")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Non-blocking process execution")
        print("   - Process lifecycle control")
        print("   - Timeout protection")
        print("   - Resource management")
        print("=" * 70)
        print()


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

        # Real-world scenarios
        print("\n" + "=" * 70)
        print("RUNNING REAL-WORLD SCENARIOS")
        print("=" * 70 + "\n")
        example.advanced_subprocess_real_world_example()

        print("\n" + "=" * 35)
        print("All advanced subprocess examples completed successfully!")

    except Exception as e:
        print(f"\nExample failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
