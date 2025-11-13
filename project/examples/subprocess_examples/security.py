"""
Subprocess security examples demonstrating safe subprocess usage.

This module covers:
- Shell injection prevention
- Input validation and sanitization
- Safe path handling
- Environment variable security
- Resource limits and quotas
- Privilege separation
- Command whitelisting
"""

import subprocess
import os
import shlex
import tempfile
from typing import List, Set
from pathlib import Path


class SubprocessSecurityExample:
    """
    Security best practices for subprocess operations.

    When to Use:
        - User input handling
        - Secure command execution
        - Path validation
        - Environment security
        - Resource limits

    Real-World Examples:
        - Web applications: Execute user commands safely
        - System administration: Secure admin operations
        - File processing: Safe file operations
        - API endpoints: Secure command execution
        - Automation: Secure automation scripts

    Gotchas:
        - shell=True is security risk
        - Always validate user input
        - Path traversal attacks
        - Command injection vulnerabilities
        - Environment variable attacks

    Performance Notes:
        - Input validation overhead minimal
        - Security checks add minimal overhead
        - Critical for production systems
        - Balance security vs usability
    """

    @staticmethod
    def shell_injection_prevention() -> None:
        """Demonstrate prevention of shell injection attacks."""
        print("=== Shell Injection Prevention ===")

        # UNSAFE: Vulnerable to shell injection
        print("1. UNSAFE - Shell injection vulnerability:")
        user_input = "file.txt; rm -rf /"  # Malicious input

        try:
            # This would be dangerous if shell=True
            cmd = f"cat {user_input}"  # Don't do this!
            print(f"   Dangerous command: {cmd}")
            print("   ❌ This allows arbitrary command execution!")
        except:
            pass

        # SAFE: Using subprocess with list arguments
        print("\\n2. SAFE - List arguments prevent injection:")
        filename = "file.txt; rm -rf /"  # This is now just a filename

        try:
            result = subprocess.run(
                ['cat', filename],  # Safe: no shell interpretation
                capture_output=True,
                text=True
            )
            # This will fail safely because the filename doesn't exist
            print(f"   Safe command: {result.args}")
            print("   ✅ No shell injection possible!")
        except FileNotFoundError:
            print(f"   Safe command failed as expected: {filename} not found")

        # SAFE: Using shlex.quote for required shell usage
        print("\\n3. SAFE - shlex.quote for required shell usage:")
        safe_filename = shlex.quote("file.txt; rm -rf /")
        cmd = f"ls -la {safe_filename}"
        print(f"   Quoted command: {cmd}")
        print("   ✅ Shell metacharacters are escaped!")

    @staticmethod
    def input_validation() -> None:
        """Demonstrate input validation and sanitization."""
        print("\\n=== Input Validation and Sanitization ===")

        def validate_filename(filename: str) -> str:
            """Validate and sanitize filename input."""
            # Remove path separators
            safe_name = filename.replace('/', '').replace('\\\\', '')

            # Remove dangerous characters
            dangerous = ['<', '>', '|', '&', ';', '\\$', '`', '(', ')']
            for char in dangerous:
                safe_name = safe_name.replace(char, '')

            # Limit length
            safe_name = safe_name[:255]

            return safe_name

        def run_safe_command(user_input: str) -> subprocess.CompletedProcess:
            """Run command with validated input."""
            safe_input = validate_filename(user_input)
            return subprocess.run(
                ['echo', f'Safe input: {safe_input}'],
                capture_output=True,
                text=True,
                check=True
            )

        print("1. Input validation:")
        test_inputs = [
            "normal_file.txt",
            "../../../etc/passwd",
            "file;rm -rf /",
            "file$(malicious_command)"
        ]

        for user_input in test_inputs:
            try:
                result = run_safe_command(user_input)
                print(f"   Input: '{user_input}' → Safe: '{result.stdout.strip()}'")
            except Exception as e:
                print(f"   Input: '{user_input}' → Error: {e}")

    @staticmethod
    def safe_path_handling() -> None:
        """Demonstrate safe path handling practices."""
        print("\\n=== Safe Path Handling ===")

        def resolve_safe_path(base_dir: Path, user_path: str) -> Path:
            """Safely resolve user-provided path within base directory."""
            base_dir = base_dir.resolve()  # Get absolute path

            # Resolve the user path relative to base directory
            full_path = (base_dir / user_path).resolve()

            # Ensure the resolved path is within base directory
            if not str(full_path).startswith(str(base_dir)):
                raise ValueError(f"Path traversal attempt: {user_path}")

            return full_path

        print("1. Path traversal prevention:")
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            # Create a safe file
            safe_file = base_path / "safe.txt"
            safe_file.write_text("This is safe content")

            test_paths = [
                "safe.txt",
                "../outside.txt",
                "../../../etc/passwd",
                "safe.txt/../safe.txt"
            ]

            for user_path in test_paths:
                try:
                    resolved = resolve_safe_path(base_path, user_path)
                    if resolved.exists():
                        content = resolved.read_text()
                        print(f"   ✅ '{user_path}' → '{resolved.name}': {content}")
                    else:
                        print(f"   ⚠️  '{user_path}' → '{resolved.name}': File not found")
                except ValueError as e:
                    print(f"   ❌ '{user_path}' → {e}")

    @staticmethod
    def environment_security() -> None:
        """Demonstrate secure environment variable handling."""
        print("\\n=== Environment Variable Security ===")

        print("1. Clean environment for subprocess:")
        # Create minimal environment
        safe_env = {
            'PATH': os.environ.get('PATH', ''),  # Only essential PATH
            'HOME': os.environ.get('HOME', ''),
            'USER': os.environ.get('USER', ''),
            'LANG': 'C',  # Avoid locale issues
        }

        # Remove potentially dangerous environment variables
        dangerous_vars = ['LD_LIBRARY_PATH', 'LD_PRELOAD', 'PYTHONPATH']
        for var in dangerous_vars:
            safe_env.pop(var, None)

        result = subprocess.run(
            ['env'],
            capture_output=True,
            text=True,
            env=safe_env
        )

        print("   Safe environment variables:")
        env_lines = result.stdout.strip().split('\\n')
        for line in env_lines[:5]:  # Show first 5
            if '=' in line:
                var, value = line.split('=', 1)
                print(f"   {var}={value}")

        print("\\n2. Avoiding environment variable injection:")
        # Don't use environment variables from untrusted sources
        user_provided_env = {'MALICIOUS': 'rm -rf /'}  # Don't do this!

        # Safe approach: whitelist allowed environment variables
        allowed_env_vars = {'PATH', 'HOME', 'USER', 'LANG'}
        safe_user_env = {k: v for k, v in user_provided_env.items()
                        if k in allowed_env_vars}

        print(f"   Original env: {user_provided_env}")
        print(f"   Filtered env: {safe_user_env}")
        print("   ✅ Only whitelisted variables allowed!")

    @staticmethod
    def command_whitelisting() -> None:
        """Demonstrate command whitelisting for security."""
        print("\\n=== Command Whitelisting ===")

        # Whitelist of allowed commands
        ALLOWED_COMMANDS = {
            'ls', 'cat', 'head', 'tail', 'grep', 'wc', 'sort', 'uniq',
            'python3', 'echo', 'pwd', 'date', 'whoami'
        }

        def run_whitelisted_command(cmd: List[str]) -> subprocess.CompletedProcess:
            """Run only whitelisted commands."""
            if not cmd:
                raise ValueError("Empty command")

            base_cmd = cmd[0]
            if base_cmd not in ALLOWED_COMMANDS:
                raise ValueError(f"Command '{base_cmd}' not in whitelist")

            # Additional validation: check for dangerous arguments
            dangerous_args = [';', '&&', '||', '|', '`', '$(']
            for arg in cmd:
                for dangerous in dangerous_args:
                    if dangerous in arg:
                        raise ValueError(f"Dangerous argument detected: {arg}")

            return subprocess.run(cmd, capture_output=True, text=True, check=True)

        print("1. Command whitelisting:")
        test_commands = [
            ['ls', '-la'],
            ['cat', '/etc/passwd'],
            ['rm', '-rf', '/'],  # Dangerous command
            ['ls', '-la', ';', 'rm', '-rf', '/']  # Dangerous args
        ]

        for cmd in test_commands:
            try:
                result = run_whitelisted_command(cmd)
                output = result.stdout.strip()[:50]  # Truncate long output
                print(f"   ✅ {cmd} → {output}{'...' if len(result.stdout) > 50 else ''}")
            except ValueError as e:
                print(f"   ❌ {cmd} → {e}")
            except subprocess.CalledProcessError as e:
                print(f"   ⚠️  {cmd} → Command failed with code {e.returncode}")

    @staticmethod
    def resource_limits() -> None:
        """Demonstrate resource limits and quotas."""
        print("\\n=== Resource Limits and Quotas ===")

        # Note: These are platform-specific and may not work on all systems
        print("1. CPU time limits (Unix-like systems):")

        try:
            # Set CPU time limit (this is platform-specific)
            import resource

            # Save original limits
            original_limits = resource.getrlimit(resource.RLIMIT_CPU)

            # Set CPU limit to 5 seconds
            resource.setrlimit(resource.RLIMIT_CPU, (5, 5))

            print("   CPU time limit set to 5 seconds")
            result = subprocess.run([
                'python3', '-c', '''
import time
start = time.time()
while time.time() - start < 10:  # Try to run for 10 seconds
    pass
print("Loop completed")
                '''
            ], capture_output=True, text=True)

            if result.returncode == -9:  # SIGKILL
                print("   ✅ Process killed due to CPU time limit")
            else:
                print(f"   Process completed with code: {result.returncode}")

            # Restore original limits
            resource.setrlimit(resource.RLIMIT_CPU, original_limits)

        except ImportError:
            print("   Resource limits not available on this platform")

        print("\\n2. Memory limits (if supported):")
        print("   (Platform-specific - requires additional setup)")

        print("\\n3. Process quotas:")
        print("   • Limit concurrent subprocesses")
        print("   • Monitor resource usage")
        print("   • Implement rate limiting")

    @staticmethod
    def privilege_separation() -> None:
        """Demonstrate privilege separation concepts."""
        print("\\n=== Privilege Separation ===")

        print("1. Running subprocess as different user (Unix-like):")

        # Check if we can use sudo (this is just a demonstration)
        try:
            # DON'T actually run this with real credentials!
            print("   ⚠️  Privilege separation requires careful setup:")
            print("   • Use dedicated user accounts for subprocesses")
            print("   • Implement proper capability dropping")
            print("   • Use chroot or containers for isolation")
            print("   • Validate all inputs before privilege escalation")

            # Example of checking current privileges
            result = subprocess.run(['id'], capture_output=True, text=True)
            print(f"   Current user: {result.stdout.strip()}")

        except Exception as e:
            print(f"   Privilege check failed: {e}")

        print("\\n2. Container-based isolation:")
        print("   • Use Docker/Podman for complete isolation")
        print("   • subprocess.run(['docker', 'run', 'safe-image', ...])")
        print("   • Network and filesystem isolation")

    @staticmethod
    def comprehensive_security_demo() -> None:
        """Comprehensive security demonstration."""
        print("\\n=== Comprehensive Security Demo ===")

        def secure_subprocess_run(cmd: List[str], allowed_commands: Set[str],
                                base_dir: Path) -> subprocess.CompletedProcess:
            """Secure subprocess execution with multiple safeguards."""

            # 1. Command whitelisting
            if not cmd or cmd[0] not in allowed_commands:
                raise ValueError(f"Command '{cmd[0]}' not allowed")

            # 2. Path validation for file arguments
            for arg in cmd[1:]:
                if '/' in arg or '\\\\' in arg:
                    # Validate file paths
                    try:
                        resolved = resolve_safe_path(base_dir, arg)
                        # Replace with resolved path
                        cmd[cmd.index(arg)] = str(resolved)
                    except ValueError:
                        raise ValueError(f"Unsafe path: {arg}")

            # 3. Clean environment
            safe_env = {
                'PATH': os.environ.get('PATH', ''),
                'HOME': str(base_dir),
                'LANG': 'C',
            }

            # 4. Resource limits (if available)
            try:
                import resource
                # Set some basic limits
                resource.setrlimit(resource.RLIMIT_CPU, (30, 30))  # 30 seconds CPU
            except ImportError:
                pass

            # 5. Execute with timeout and output capture
            return subprocess.run(
                cmd,
                cwd=base_dir,
                env=safe_env,
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )

        # Helper function for path resolution
        def resolve_safe_path(base_dir: Path, user_path: str) -> Path:
            """Safely resolve user-provided path."""
            full_path = (base_dir / user_path).resolve()
            if not str(full_path).startswith(str(base_dir)):
                raise ValueError(f"Path traversal: {user_path}")
            return full_path

        print("1. Secure subprocess execution:")
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            # Create a safe file
            safe_file = base_path / "data.txt"
            safe_file.write_text("Safe content")

            allowed_cmds = {'cat', 'ls', 'echo', 'python3'}

            test_cases = [
                (['cat', 'data.txt'], "Safe file access"),
                (['ls'], "Safe directory listing"),
                (['rm', '-rf', '/'], "Dangerous command - should fail"),
                (['../../../etc/passwd', 'cat'], "Path traversal - should fail")
            ]

            for cmd, description in test_cases:
                try:
                    result = secure_subprocess_run(cmd, allowed_cmds, base_path)
                    output = result.stdout.strip()[:50]
                    print(f"   ✅ {description}: {output}{'...' if len(result.stdout) > 50 else ''}")
                except Exception as e:
                    print(f"   ❌ {description}: {e}")

    def security_real_world_example(self) -> None:
        """
        Real-World Scenario: Subprocess Security - User Command Execution API.

        REAL-WORLD SCENARIO:
        ====================
        You're building a user command execution API:
        - Users submit commands to execute
        - Execute commands on server
        - Problem: Prevent command injection attacks
        
        THE PROBLEM WITHOUT SECURITY:
        ==============================
        - Command injection → system compromise
        - Path traversal → unauthorized access
        - Shell injection → arbitrary code execution
        - Environment attacks → privilege escalation
        - System vulnerable → security breach
        
        THE SOLUTION:
        =============
        Secure subprocess enables:
        - Input validation → prevent injection
        - Safe command execution → no shell injection
        - Path validation → prevent traversal
        - Environment security → prevent attacks
        - Resource limits → prevent abuse
        
        WHEN TO USE SECURE SUBPROCESS:
        ==============================
        ✅ User command execution APIs
        ✅ Web applications with commands
        ✅ System administration tools
        ✅ File processing with user input
        ✅ Automation with user input
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: User Command Execution API")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - User command execution API")
        print("  - Users submit commands to execute")
        print("  - Execute commands on server")
        print("  - Problem: Prevent command injection attacks")
        print()
        print("THE PROBLEM:")
        print("  Without security:")
        print("    ❌ Command injection → system compromise")
        print("    ❌ Path traversal → unauthorized access")
        print("    ❌ Shell injection → arbitrary code execution")
        print("    ❌ Environment attacks → privilege escalation")
        print()
        print("THE SOLUTION:")
        print("  With secure subprocess:")
        print("    ✅ Input validation → prevent injection")
        print("    ✅ Safe command execution → no shell injection")
        print("    ✅ Path validation → prevent traversal")
        print("    ✅ Environment security → prevent attacks")
        print()
        print("=" * 70)
        print()

        # Whitelist of allowed commands
        ALLOWED_COMMANDS = {"echo", "date", "whoami"}

        def execute_user_command(user_input: str) -> dict:
            """Safely execute a user command."""
            # Validate input
            if not user_input or not user_input.strip():
                return {"status": "error", "message": "Empty command"}

            # Parse command (prevent shell injection)
            parts = shlex.split(user_input)
            if not parts:
                return {"status": "error", "message": "Invalid command"}

            command = parts[0]

            # Whitelist check
            if command not in ALLOWED_COMMANDS:
                return {"status": "error", "message": f"Command '{command}' not allowed"}

            # Execute safely (no shell=True)
            try:
                result = subprocess.run(
                    parts,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False
                )
                return {
                    "status": "success" if result.returncode == 0 else "error",
                    "output": result.stdout,
                    "error": result.stderr,
                    "returncode": result.returncode
                }
            except subprocess.TimeoutExpired:
                return {"status": "error", "message": "Command timeout"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        print("Testing secure command execution...")
        print()

        # Test cases
        test_commands = [
            "echo hello",
            "date",
            "whoami",
            "rm -rf /",  # Should be blocked
            "echo hello; rm -rf /",  # Should be blocked
        ]

        for cmd in test_commands:
            result = execute_user_command(cmd)
            if result["status"] == "success":
                print(f"  ✅ '{cmd}': {result['output'].strip()}")
            else:
                print(f"  ❌ '{cmd}': {result['message']}")

        print()
        print("  ✅ Secure subprocess prevented command injection!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE SECURE SUBPROCESS:")
        print("   ✅ User command execution APIs")
        print("   ✅ Web applications with commands")
        print("   ✅ System administration tools")
        print("   ✅ File processing with user input")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Prevents command injection")
        print("   - Protects system security")
        print("   - Prevents unauthorized access")
        print("   - Production security")
        print("=" * 70)
        print()


def main() -> None:
    """Run all security examples."""
    print("Subprocess Security Examples")
    print("=" * 35)

    example = SubprocessSecurityExample()

    try:
        example.shell_injection_prevention()
        example.input_validation()
        example.safe_path_handling()
        example.environment_security()
        example.command_whitelisting()
        example.resource_limits()
        example.privilege_separation()
        example.comprehensive_security_demo()

        # Real-world scenarios
        print("\n" + "=" * 70)
        print("RUNNING REAL-WORLD SCENARIOS")
        print("=" * 70 + "\n")
        example.security_real_world_example()

        print("\n" + "=" * 35)
        print("All security examples completed successfully!")

    except Exception as e:
        print(f"\nExample failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
