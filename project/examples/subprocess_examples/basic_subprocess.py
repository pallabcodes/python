"""
Basic subprocess examples demonstrating subprocess.run() and subprocess.call().

This module covers:
- Basic command execution with subprocess.run()
- Capturing output and error streams
- Return codes and exit status
- Simple subprocess.call() usage
- Text vs binary output handling
"""

import subprocess
import sys
import os
from typing import Optional


class BasicSubprocessExample:
    """
    Basic examples of subprocess usage for external command execution.

    When to Use:
        - Executing external commands
        - Running shell commands from Python
        - Capturing command output
        - Checking command exit codes
        - Simple command execution

    Real-World Examples:
        - System administration: Run system commands
        - Build scripts: Execute build tools
        - DevOps: Run deployment commands
        - Testing: Execute test commands
        - Automation: Automate command execution

    Gotchas:
        - shell=True is security risk (use list args)
        - Always validate user input
        - Handle return codes properly
        - Capture output to prevent blocking
        - Use text=True for string output

    Performance Notes:
        - Process creation overhead
        - Blocking until completion
        - Use Popen for non-blocking
        - Consider async subprocess for I/O
    """

    @staticmethod
    def basic_run_command() -> None:
        """Demonstrate basic subprocess.run() usage."""
        print("=== Basic subprocess.run() Usage ===")

        # Simple command execution
        print("1. Simple command execution:")
        result = subprocess.run(['echo', 'Hello, subprocess!'])
        print(f"   Return code: {result.returncode}")

        # Command with arguments
        print("\n2. Command with arguments:")
        result = subprocess.run(['echo', 'Hello', 'World', 'from', 'Python!'])
        print(f"   Return code: {result.returncode}")

    @staticmethod
    def capturing_output() -> None:
        """Demonstrate capturing stdout and stderr."""
        print("\n=== Capturing Output ===")

        # Capture stdout
        print("1. Capturing stdout:")
        result = subprocess.run(['echo', 'This is captured output'],
                              capture_output=True, text=True)
        print(f"   Captured output: '{result.stdout.strip()}'")
        print(f"   Return code: {result.returncode}")

        # Capture both stdout and stderr
        print("\n2. Capturing both stdout and stderr:")
        result = subprocess.run(['python3', '-c', 'print("stdout"); import sys; print("stderr", file=sys.stderr)'],
                              capture_output=True, text=True)
        print(f"   stdout: '{result.stdout.strip()}'")
        print(f"   stderr: '{result.stderr.strip()}'")

        # Binary output
        print("\n3. Binary output (not captured as text):")
        result = subprocess.run(['echo', 'binary data'],
                              capture_output=True)  # No text=True
        print(f"   Raw bytes: {result.stdout}")
        print(f"   As string: '{result.stdout.decode().strip()}'")

    @staticmethod
    def return_codes() -> None:
        """Demonstrate handling return codes."""
        print("\n=== Return Codes and Exit Status ===")

        # Successful command
        print("1. Successful command:")
        result = subprocess.run(['true'])  # Unix true command
        print(f"   Command: true")
        print(f"   Return code: {result.returncode}")
        print(f"   Success: {result.returncode == 0}")

        # Failed command
        print("\n2. Failed command:")
        result = subprocess.run(['false'])  # Unix false command
        print(f"   Command: false")
        print(f"   Return code: {result.returncode}")
        print(f"   Success: {result.returncode == 0}")

        # Custom return code
        print("\n3. Custom return code:")
        result = subprocess.run(['python3', '-c', 'import sys; sys.exit(42)'])
        print(f"   Command: python3 -c 'exit(42)'")
        print(f"   Return code: {result.returncode}")

    @staticmethod
    def subprocess_call() -> None:
        """Demonstrate subprocess.call() usage."""
        print("\n=== subprocess.call() Usage ===")

        print("1. subprocess.call() - returns exit code directly:")
        exit_code = subprocess.call(['echo', 'Called with subprocess.call()'])
        print(f"   Exit code: {exit_code}")

        print("\n2. subprocess.call() with shell=True:")
        exit_code = subprocess.call('echo "Shell execution" && true', shell=True)
        print(f"   Exit code: {exit_code}")

    @staticmethod
    def text_vs_binary() -> None:
        """Demonstrate text vs binary output handling."""
        print("\n=== Text vs Binary Output ===")

        # Text output (text=True)
        print("1. Text output:")
        result = subprocess.run(['python3', '-c', 'print("Hello, 世界!")'],
                              capture_output=True, text=True)
        print(f"   Text output: {result.stdout.strip()}")
        print(f"   Type: {type(result.stdout)}")

        # Binary output
        print("\n2. Binary output:")
        result = subprocess.run(['python3', '-c', 'print("Hello, 世界!")'],
                              capture_output=True)  # No text=True
        print(f"   Binary output: {result.stdout}")
        print(f"   Type: {type(result.stdout)}")
        print(f"   Decoded: {result.stdout.decode('utf-8').strip()}")

    @staticmethod
    def environment_variables() -> None:
        """Demonstrate environment variable handling."""
        print("\n=== Environment Variables ===")

        # Inherit environment
        print("1. Inherit parent environment:")
        result = subprocess.run(['env'], capture_output=True, text=True)
        env_vars = result.stdout.strip().split('\n')
        print(f"   Environment variables: {len(env_vars)} total")
        # Show first few
        for var in env_vars[:3]:
            print(f"   {var}")

        # Custom environment
        print("\n2. Custom environment:")
        custom_env = {'CUSTOM_VAR': 'Hello from subprocess!', 'PATH': os.environ['PATH']}
        result = subprocess.run(['python3', '-c', 'import os; print(os.environ.get("CUSTOM_VAR"))'],
                              env=custom_env, capture_output=True, text=True)
        print(f"   Custom env output: {result.stdout.strip()}")

    @staticmethod
    def working_directory() -> None:
        """Demonstrate working directory control."""
        print("\n=== Working Directory ===")

        # Default working directory
        print("1. Default working directory:")
        result = subprocess.run(['pwd'], capture_output=True, text=True)
        print(f"   Current directory: {result.stdout.strip()}")

        # Custom working directory
        print("\n2. Custom working directory:")
        temp_dir = '/tmp' if os.path.exists('/tmp') else os.getcwd()
        result = subprocess.run(['pwd'], capture_output=True, text=True, cwd=temp_dir)
        print(f"   Working directory: {result.stdout.strip()}")
        print(f"   Requested: {temp_dir}")

    def basic_subprocess_real_world_example(self) -> None:
        """
        Real-World Scenario: Basic Subprocess - System Health Check Script.

        REAL-WORLD SCENARIO:
        ====================
        You're building a system health check script:
        - Run multiple system commands to check health
        - Capture output for analysis
        - Problem: Need to execute commands reliably
        
        THE PROBLEM WITHOUT SUBPROCESS:
        ================================
        - Manual command execution → error-prone
        - No output capture → can't analyze
        - No error handling → script fails
        - Inconsistent execution → unreliable
        - System administration → manual work
        
        THE SOLUTION:
        =============
        Basic subprocess enables:
        - Execute system commands → reliable
        - Capture output → analyze results
        - Handle errors → robust scripts
        - Consistent execution → reliable
        - Automation → efficient
        
        WHEN TO USE BASIC SUBPROCESS:
        =============================
        ✅ System administration scripts
        ✅ Health check scripts
        ✅ Build automation
        ✅ Deployment scripts
        ✅ Command execution automation
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: System Health Check Script")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - System health check script")
        print("  - Run multiple system commands to check health")
        print("  - Capture output for analysis")
        print("  - Problem: Need to execute commands reliably")
        print()
        print("THE PROBLEM:")
        print("  Without subprocess:")
        print("    ❌ Manual command execution → error-prone")
        print("    ❌ No output capture → can't analyze")
        print("    ❌ No error handling → script fails")
        print("    ❌ Inconsistent execution → unreliable")
        print()
        print("THE SOLUTION:")
        print("  With basic subprocess:")
        print("    ✅ Execute system commands → reliable")
        print("    ✅ Capture output → analyze results")
        print("    ✅ Handle errors → robust scripts")
        print("    ✅ Consistent execution → reliable")
        print()
        print("=" * 70)
        print()

        # Health check commands
        health_checks = [
            ("System uptime", ["uptime"]),
            ("Disk usage", ["df", "-h"]),
            ("Memory info", ["free", "-h"] if sys.platform != "darwin" else ["vm_stat"]),
        ]

        print("Running system health checks...")
        print()

        results = {}
        for check_name, command in health_checks:
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False
                )
                if result.returncode == 0:
                    results[check_name] = {"status": "OK", "output": result.stdout.strip()}
                    print(f"  ✅ {check_name}: OK")
                else:
                    results[check_name] = {"status": "ERROR", "output": result.stderr.strip()}
                    print(f"  ❌ {check_name}: ERROR")
            except subprocess.TimeoutExpired:
                results[check_name] = {"status": "TIMEOUT", "output": ""}
                print(f"  ⏱️  {check_name}: TIMEOUT")
            except Exception as e:
                results[check_name] = {"status": "EXCEPTION", "output": str(e)}
                print(f"  ❌ {check_name}: EXCEPTION - {e}")

        print()
        print("Health check summary:")
        for check_name, result in results.items():
            print(f"  {check_name}: {result['status']}")
        print()
        print("  ✅ Basic subprocess enabled reliable command execution!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE BASIC SUBPROCESS:")
        print("   ✅ System administration scripts")
        print("   ✅ Health check scripts")
        print("   ✅ Build automation")
        print("   ✅ Deployment scripts")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Reliable command execution")
        print("   - Output capture for analysis")
        print("   - Error handling")
        print("   - Automation")
        print("=" * 70)
        print()


def main() -> None:
    """Run all basic subprocess examples."""
    print("Basic Subprocess Examples")
    print("=" * 30)

    example = BasicSubprocessExample()

    try:
        example.basic_run_command()
        example.capturing_output()
        example.return_codes()
        example.subprocess_call()
        example.text_vs_binary()
        example.environment_variables()
        example.working_directory()

        # Real-world scenarios
        print("\n" + "=" * 70)
        print("RUNNING REAL-WORLD SCENARIOS")
        print("=" * 70 + "\n")
        example.basic_subprocess_real_world_example()

        print("\n" + "=" * 30)
        print("All basic subprocess examples completed successfully!")

    except Exception as e:
        print(f"\nExample failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
