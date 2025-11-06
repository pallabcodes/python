"""
Subprocess error handling examples demonstrating robust error management.

This module covers:
- Exception handling patterns
- Timeout management
- Process cleanup
- Error propagation
- Recovery strategies
- Logging and monitoring
"""

import subprocess
import time
import signal
import logging
import os
from typing import Optional, Dict, Any
from contextlib import contextmanager


class SubprocessErrorHandlingExample:
    """
    Comprehensive error handling patterns for subprocess operations.
    """

    @staticmethod
    def basic_error_handling() -> None:
        """Demonstrate basic error handling with subprocess.run()."""
        print("=== Basic Error Handling ===")

        print("1. Handling command not found:")
        try:
            result = subprocess.run(['nonexistent_command'],
                                  capture_output=True, text=True, check=True)
        except FileNotFoundError as e:
            print(f"   Command not found: {e}")
        except subprocess.CalledProcessError as e:
            print(f"   Command failed: {e}")

        print("\n2. Handling command failure with check=True:")
        try:
            result = subprocess.run(['python3', '-c', 'import sys; sys.exit(1)'],
                                  capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"   Command failed with exit code {e.returncode}")
            print(f"   stdout: '{e.stdout.strip()}'")
            print(f"   stderr: '{e.stderr.strip()}'")

        print("\n3. Handling command failure without check=True:")
        result = subprocess.run(['python3', '-c', 'import sys; sys.exit(1)'],
                              capture_output=True, text=True)
        print(f"   Command failed with exit code {result.returncode}")
        print(f"   No exception raised, manual checking needed")

    @staticmethod
    def timeout_error_handling() -> None:
        """Demonstrate timeout handling and recovery."""
        print("\n=== Timeout Error Handling ===")

        print("1. Handling timeout with communicate():")
        process = subprocess.Popen(
            ['python3', '-c', 'import time; time.sleep(10); print("Done")'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = process.communicate(timeout=2)
            print(f"   Process completed: {stdout.strip()}")
        except subprocess.TimeoutExpired:
            print("   Process timed out after 2 seconds")
            # Clean up the process
            process.kill()
            # Wait for the process to actually terminate
            try:
                process.wait(timeout=5)
                print("   Process cleaned up successfully")
            except subprocess.TimeoutExpired:
                print("   Process didn't terminate gracefully")
                process.terminate()
                process.wait()

    @staticmethod
    def signal_error_handling() -> None:
        """Demonstrate signal handling and interruption recovery."""
        print("\n=== Signal Handling and Recovery ===")

        print("1. Handling keyboard interrupt during subprocess:")
        try:
            print("   Starting long-running subprocess (Ctrl+C to interrupt)...")
            result = subprocess.run(
                ['python3', '-c', '''
import time
print("Subprocess started")
for i in range(20):
    print(f"Progress: {i+1}/20", end="\\r", flush=True)
    time.sleep(0.5)
print("\\nSubprocess completed")
                '''],
                timeout=5  # This will cause TimeoutExpired
            )
        except subprocess.TimeoutExpired:
            print("   \\nSubprocess timed out (simulating interrupt)")
        except KeyboardInterrupt:
            print("   \\nKeyboard interrupt received")
            print("   Cleaning up subprocess...")

    @staticmethod
    def resource_cleanup() -> None:
        """Demonstrate proper resource cleanup patterns."""
        print("\n=== Resource Cleanup Patterns ===")

        print("1. Manual cleanup:")
        process = subprocess.Popen(
            ['python3', '-c', 'import time; time.sleep(2); print("Done")'],
            stdout=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = process.communicate(timeout=1)
            print(f"   Process completed: {stdout.strip()}")
        except subprocess.TimeoutExpired:
            print("   Process timed out, cleaning up...")
            process.kill()
            process.wait()  # Wait for cleanup
            print("   Process cleaned up")

        print("\n2. Context manager for automatic cleanup:")
        @contextmanager
        def managed_subprocess(cmd, **kwargs):
            process = subprocess.Popen(cmd, **kwargs)
            try:
                yield process
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()

        try:
            with managed_subprocess(
                ['python3', '-c', 'import time; time.sleep(3); print("Managed")'],
                stdout=subprocess.PIPE,
                text=True
            ) as proc:
                stdout, stderr = proc.communicate(timeout=1)
                print(f"   Managed process: {stdout.strip()}")
        except subprocess.TimeoutExpired:
            print("   Managed process timed out, automatic cleanup occurred")

    @staticmethod
    def retry_and_recovery() -> None:
        """Demonstrate retry patterns and recovery strategies."""
        print("\n=== Retry Patterns and Recovery ===")

        def run_with_retry(cmd, max_retries=3, delay=1):
            """Run a command with retry logic."""
            for attempt in range(max_retries):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True,
                                          timeout=5, check=True)
                    return result
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
                        FileNotFoundError) as e:
                    print(f"   Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        print(f"   Retrying in {delay} seconds...")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        raise

        print("1. Retry with exponential backoff:")
        try:
            # This will fail a few times before succeeding
            result = run_with_retry([
                'python3', '-c', '''
import random
if random.random() < 0.7:  # 70% failure rate
    import sys
    sys.exit(1)
print("Success!")
                '''
            ])
            print(f"   Final result: {result.stdout.strip()}")
        except Exception as e:
            print(f"   All retries failed: {e}")

    @staticmethod
    def logging_and_monitoring() -> None:
        """Demonstrate logging and monitoring of subprocess operations."""
        print("\n=== Logging and Monitoring ===")

        # Setup logging
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)

        def log_subprocess_run(cmd, **kwargs):
            """Run subprocess with comprehensive logging."""
            logger.info(f"Starting subprocess: {' '.join(cmd)}")

            start_time = time.time()
            try:
                result = subprocess.run(cmd, **kwargs)
                duration = time.time() - start_time

                if result.returncode == 0:
                    logger.info(".2f")
                else:
                    logger.error(".2f")

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(".2f")
                raise

        print("1. Logged subprocess execution:")
        try:
            result = log_subprocess_run(
                ['python3', '-c', 'print("Logged subprocess execution")'],
                capture_output=True, text=True
            )
        except Exception as e:
            print(f"   Logged error: {e}")

    @staticmethod
    def graceful_degradation() -> None:
        """Demonstrate graceful degradation when subprocesses fail."""
        print("\n=== Graceful Degradation ===")

        def run_command_with_fallback(primary_cmd, fallback_cmd):
            """Try primary command, fall back to secondary if it fails."""
            try:
                print(f"   Trying primary command: {' '.join(primary_cmd)}")
                result = subprocess.run(primary_cmd, capture_output=True,
                                      text=True, timeout=5, check=True)
                print(f"   Primary command succeeded")
                return result
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
                    FileNotFoundError) as e:
                print(f"   Primary command failed: {e}")
                print(f"   Falling back to: {' '.join(fallback_cmd)}")
                try:
                    result = subprocess.run(fallback_cmd, capture_output=True,
                                          text=True, timeout=5, check=True)
                    print(f"   Fallback command succeeded")
                    return result
                except Exception as e2:
                    print(f"   Fallback also failed: {e2}")
                    raise

        print("1. Primary command with fallback:")
        try:
            result = run_command_with_fallback(
                ['python3', '-c', 'import nonexistent_module'],  # Will fail
                ['python3', '-c', 'print("Fallback: Hello World")']  # Will succeed
            )
            print(f"   Final result: {result.stdout.strip()}")
        except Exception as e:
            print(f"   Both commands failed: {e}")

    @staticmethod
    def error_propagation() -> None:
        """Demonstrate error propagation patterns."""
        print("\n=== Error Propagation Patterns ===")

        class SubprocessError(Exception):
            """Custom exception for subprocess errors."""
            def __init__(self, cmd, returncode, stdout, stderr):
                self.cmd = cmd
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr
                super().__init__(f"Command '{' '.join(cmd)}' failed with code {returncode}")

        def run_with_custom_error(cmd, **kwargs):
            """Run subprocess and raise custom exception on failure."""
            try:
                result = subprocess.run(cmd, **kwargs, check=True)
                return result
            except subprocess.CalledProcessError as e:
                raise SubprocessError(
                    cmd=e.cmd,
                    returncode=e.returncode,
                    stdout=e.stdout,
                    stderr=e.stderr
                ) from e

        print("1. Custom error propagation:")
        try:
            result = run_with_custom_error([
                'python3', '-c', 'import sys; sys.exit(1)'
            ], capture_output=True, text=True)
        except SubprocessError as e:
            print(f"   Custom error caught:")
            print(f"   Command: {' '.join(e.cmd)}")
            print(f"   Return code: {e.returncode}")
            print(f"   stdout: '{e.stdout.strip()}'")
            print(f"   stderr: '{e.stderr.strip()}'")

    @staticmethod
    def comprehensive_error_demo() -> None:
        """Comprehensive error handling demonstration."""
        print("\n=== Comprehensive Error Handling Demo ===")

        def robust_subprocess_run(cmd, retries=2, timeout=10):
            """Robust subprocess execution with comprehensive error handling."""
            last_exception = None

            for attempt in range(retries + 1):
                try:
                    print(f"   Attempt {attempt + 1}/{retries + 1}: {' '.join(cmd)}")

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        check=True
                    )

                    print(f"   ✅ Success on attempt {attempt + 1}")
                    return result

                except subprocess.TimeoutExpired as e:
                    last_exception = e
                    print(f"   ⏱️  Timeout after {timeout}s")
                except subprocess.CalledProcessError as e:
                    last_exception = e
                    print(f"   ❌ Exit code {e.returncode}")
                    if e.stderr:
                        print(f"   Error: {e.stderr.strip()}")
                except FileNotFoundError as e:
                    last_exception = e
                    print(f"   📁 Command not found: {e}")
                    break  # No point retrying if command doesn't exist
                except Exception as e:
                    last_exception = e
                    print(f"   💥 Unexpected error: {e}")

                if attempt < retries:
                    delay = 2 ** attempt  # Exponential backoff
                    print(f"   🔄 Retrying in {delay} seconds...")
                    time.sleep(delay)

            print(f"   💔 All {retries + 1} attempts failed")
            raise last_exception

        print("1. Robust subprocess execution:")
        # Test with a command that might fail
        try:
            result = robust_subprocess_run([
                'python3', '-c', '''
import random
import sys
if random.random() < 0.6:  # 60% chance of failure
    print("Command failed randomly", file=sys.stderr)
    sys.exit(1)
print("Success!")
                '''
            ])
            print(f"   Final result: {result.stdout.strip()}")
        except Exception as e:
            print(f"   All attempts failed: {type(e).__name__}")


def main() -> None:
    """Run all error handling examples."""
    print("Subprocess Error Handling Examples")
    print("=" * 40)

    example = SubprocessErrorHandlingExample()

    try:
        example.basic_error_handling()
        example.timeout_error_handling()
        example.signal_error_handling()
        example.resource_cleanup()
        example.retry_and_recovery()
        example.logging_and_monitoring()
        example.graceful_degradation()
        example.error_propagation()
        example.comprehensive_error_demo()

        print("\n" + "=" * 40)
        print("All error handling examples completed successfully!")

    except Exception as e:
        print(f"\nExample failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
