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

    When to Use:
        - Robust subprocess execution
        - Error recovery
        - Timeout management
        - Resource cleanup
        - Production systems

    Real-World Examples:
        - Long-running processes: Handle timeouts
        - Batch processing: Handle failures gracefully
        - System commands: Handle command errors
        - Data processing: Recover from errors
        - Automation: Robust automation

    Gotchas:
        - Zombie processes if not waited
        - Timeout handling complexity
        - Signal handling platform-specific
        - Resource cleanup required
        - Error propagation

    Performance Notes:
        - Error handling overhead minimal
        - Timeout management adds overhead
        - Critical for reliability
        - Balance timeout vs responsiveness
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
                    logger.info(
                        f"Subprocess completed successfully in {duration:.2f}s",
                        extra={"duration": duration, "returncode": result.returncode}
                    )
                else:
                    logger.error(
                        f"Subprocess failed with code {result.returncode} in {duration:.2f}s",
                        extra={"duration": duration, "returncode": result.returncode}
                    )

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Subprocess execution failed after {duration:.2f}s: {e}",
                    extra={"duration": duration, "error": str(e)},
                    exc_info=True
                )
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

    def error_handling_real_world_example(self) -> None:
        """
        Real-World Scenario: Error Handling - Batch Job Processing System.

        REAL-WORLD SCENARIO:
        ====================
        You're building a batch job processing system:
        - Process multiple jobs concurrently
        - Some jobs may fail or timeout
        - Problem: Need robust error handling
        
        THE PROBLEM WITHOUT ERROR HANDLING:
        ===================================
        - One failure stops all → system fragile
        - No timeout handling → hung processes
        - No cleanup → resource leaks
        - No retry logic → permanent failures
        - System unreliable → production issues
        
        THE SOLUTION:
        =============
        Robust error handling enables:
        - Handle failures gracefully → continue processing
        - Timeout protection → prevent hangs
        - Resource cleanup → prevent leaks
        - Retry logic → recover from transient failures
        - System reliability → production-ready
        
        WHEN TO USE ERROR HANDLING:
        ===========================
        ✅ Batch job processing
        ✅ Long-running processes
        ✅ Unreliable dependencies
        ✅ Production systems
        ✅ Critical operations
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Batch Job Processing System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Batch job processing system")
        print("  - Process multiple jobs concurrently")
        print("  - Some jobs may fail or timeout")
        print("  - Problem: Need robust error handling")
        print()
        print("THE PROBLEM:")
        print("  Without error handling:")
        print("    ❌ One failure stops all → system fragile")
        print("    ❌ No timeout handling → hung processes")
        print("    ❌ No cleanup → resource leaks")
        print("    ❌ No retry logic → permanent failures")
        print()
        print("THE SOLUTION:")
        print("  With robust error handling:")
        print("    ✅ Handle failures gracefully → continue processing")
        print("    ✅ Timeout protection → prevent hangs")
        print("    ✅ Resource cleanup → prevent leaks")
        print("    ✅ Retry logic → recover from transient failures")
        print()
        print("=" * 70)
        print()

        def process_job(job_id: int, should_fail: bool = False) -> dict:
            """Process a single job with error handling."""
            try:
                if should_fail:
                    # Simulate a failing job
                    result = subprocess.run(
                        ["python3", "-c", "import sys; sys.exit(1)"],
                        capture_output=True,
                        timeout=1.0,
                        check=False
                    )
                else:
                    # Simulate a successful job
                    result = subprocess.run(
                        ["python3", "-c", f"print('Job {job_id} completed')"],
                        capture_output=True,
                        text=True,
                        timeout=1.0,
                        check=True
                    )
                return {"job_id": job_id, "status": "success", "output": result.stdout.strip()}
            except subprocess.TimeoutExpired:
                return {"job_id": job_id, "status": "timeout", "error": "Job timeout"}
            except subprocess.CalledProcessError as e:
                return {"job_id": job_id, "status": "error", "error": str(e)}
            except Exception as e:
                return {"job_id": job_id, "status": "exception", "error": str(e)}

        print("Processing batch jobs with error handling...")
        print()

        jobs = [
            (1, False),  # Success
            (2, True),   # Failure
            (3, False),  # Success
            (4, False),  # Success
        ]

        results = []
        for job_id, should_fail in jobs:
            result = process_job(job_id, should_fail)
            results.append(result)
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"  {status_icon} Job {job_id}: {result['status']}")

        successful = sum(1 for r in results if r["status"] == "success")
        failed = len(results) - successful

        print()
        print("Batch processing summary:")
        print(f"  Total jobs: {len(results)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print("  ✅ Error handling enabled robust batch processing!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE ERROR HANDLING:")
        print("   ✅ Batch job processing")
        print("   ✅ Long-running processes")
        print("   ✅ Unreliable dependencies")
        print("   ✅ Production systems")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Handles failures gracefully")
        print("   - Prevents system crashes")
        print("   - Resource cleanup")
        print("   - Production reliability")
        print("=" * 70)
        print()


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

        # Real-world scenarios
        print("\n" + "=" * 70)
        print("RUNNING REAL-WORLD SCENARIOS")
        print("=" * 70 + "\n")
        example.error_handling_real_world_example()

        print("\n" + "=" * 40)
        print("All error handling examples completed successfully!")

    except Exception as e:
        print(f"\nExample failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
