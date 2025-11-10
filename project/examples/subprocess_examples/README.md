# Subprocess Examples

This module provides comprehensive examples of Python's `subprocess` module for running external programs and managing child processes.

## Overview

The `subprocess` module is Python's primary interface for spawning processes, connecting to their input/output/error pipes, and obtaining their return codes. Unlike `multiprocessing` which runs Python code in parallel, `subprocess` runs external executables.

## Key Concepts

- **External Programs**: Run system commands, utilities, and other executables
- **Process Management**: Control process lifecycle, I/O streams, and exit codes
- **Security**: Safe execution with input validation and environment control
- **Communication**: Various methods for data exchange with subprocesses

## Module Structure

### Core Files
- `basic_subprocess.py` - Fundamental subprocess operations
- `advanced_subprocess.py` - Process control and lifecycle management
- `communication.py` - Data exchange patterns and protocols
- `error_handling.py` - Robust error management and recovery
- `security.py` - Security best practices and input validation
- `real_world_examples.py` - Practical applications and use cases

### Utility Files
- `run_examples.py` - Test runner for all examples
- `__init__.py` - Package initialization
- `README.md` - This documentation

## Usage Examples

### Running Examples

```bash
# Run all examples
python run_examples.py all

# Run specific category
python run_examples.py basic
python run_examples.py security
python run_examples.py real

# Get help
python run_examples.py help
```

### Basic Usage

```python
import subprocess

# Simple command execution
result = subprocess.run(['ls', '-la'], capture_output=True, text=True)
print(result.stdout)

# Advanced process control
process = subprocess.Popen(['python', 'script.py'],
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          text=True)

stdout, stderr = process.communicate(input="some input")
```

## Key Differences from Other Concurrency Modules

| Module | Purpose | Process Type | Memory | Use Case |
|--------|---------|--------------|--------|----------|
| `subprocess` | External programs | Separate OS processes | Separate | System commands, utilities |
| `multiprocessing` | Python code parallelism | Python processes | Separate | CPU-bound parallel computation |
| `threading` | Concurrent execution | Threads in same process | Shared | I/O-bound concurrent tasks |
| `asyncio` | Cooperative concurrency | Single-threaded | Shared | High-concurrency I/O |

## Common Patterns

### 1. Command Execution
```python
# Simple execution
subprocess.run(['command', 'arg1', 'arg2'])

# With output capture
result = subprocess.run(['ls'], capture_output=True, text=True)
```

### 2. Process Communication
```python
# Send input, capture output
process = subprocess.Popen(['grep', 'pattern'],
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          text=True)
stdout, _ = process.communicate("input text")
```

### 3. Pipeline Processing
```python
# Command pipelines
p1 = subprocess.Popen(['cat', 'file.txt'], stdout=subprocess.PIPE)
p2 = subprocess.Popen(['grep', 'pattern'], stdin=p1.stdout,
                     stdout=subprocess.PIPE)
p1.stdout.close()
output, _ = p2.communicate()
```

### 4. Error Handling
```python
try:
    result = subprocess.run(['command'], check=True, timeout=30)
except subprocess.CalledProcessError as e:
    print(f"Command failed: {e.returncode}")
except subprocess.TimeoutExpired:
    print("Command timed out")
```

## Security Considerations

### Input Validation
- Always validate and sanitize user inputs
- Use `shlex.quote()` for shell commands
- Avoid shell=True when possible

### Environment Control
- Use `env` parameter to control environment variables
- Clean environment for subprocesses
- Avoid passing sensitive data via environment

### Command Whitelisting
- Validate commands against allowed lists
- Check for dangerous shell metacharacters
- Use absolute paths for executables

## Real-World Applications

### System Administration
- Disk usage monitoring (`df`, `du`)
- Process management (`ps`, `kill`)
- Network configuration (`ip`, `netstat`)

### Data Processing
- File manipulation (`cat`, `grep`, `sort`)
- Text processing pipelines
- Format conversion utilities

### DevOps Automation
- Build script execution
- Deployment automation
- Infrastructure monitoring

### Development Tools
- Code formatting (`black`, `prettier`)
- Linting (`flake8`, `eslint`)
- Testing (`pytest`, `jest`)

## Best Practices

### 1. Prefer List Arguments
```python
# Good
subprocess.run(['ls', '-la', '/tmp'])

# Avoid
subprocess.run('ls -la /tmp', shell=True)
```

### 2. Handle Errors Properly
```python
# Good
result = subprocess.run(['cmd'], check=True, timeout=30)

# Avoid
subprocess.call('cmd')  # Ignores errors
```

### 3. Resource Management
```python
# Good
with subprocess.Popen(['cmd']) as process:
    # Process automatically cleaned up
```

### 4. Security First
```python
# Good
subprocess.run(['cmd', safe_arg], env=safe_env)

# Avoid
subprocess.run(f'cmd {user_input}', shell=True)
```

## Performance Considerations

- **Process Creation Overhead**: Popen is more expensive than threads
- **Memory Usage**: Each subprocess has separate memory space
- **I/O Performance**: Pipe communication can be slower than shared memory
- **Scalability**: Limited by system resources (file descriptors, processes)

## Troubleshooting

### Common Issues

1. **"File not found" errors**
   - Use absolute paths or ensure PATH is set correctly
   - Check file permissions

2. **Pipe blocking**
   - Use non-blocking I/O or separate threads for reading/writing
   - Handle large data streams carefully

3. **Zombie processes**
   - Always call `.wait()` or `.communicate()` on Popen objects
   - Use context managers for automatic cleanup

4. **Encoding issues**
   - Specify `text=True` for string I/O
   - Handle encoding explicitly when needed

## Integration with Other Modules

### With Multiprocessing
```python
# Use subprocess for external tools in multiprocessing workers
def worker(task):
    # Run external command
    result = subprocess.run(['tool', task], capture_output=True)
    return result.stdout
```

### With AsyncIO
```python
# Run subprocess in asyncio event loop
import asyncio

async def async_subprocess(cmd):
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await process.communicate()
    return stdout
```

### With Threading
```python
# Run subprocess in background thread
import threading

def run_in_thread(cmd):
    def worker():
        subprocess.run(cmd)
    thread = threading.Thread(target=worker)
    thread.start()
```

## Conclusion

The `subprocess` module is essential for Python applications that need to interact with the operating system, run external tools, or perform system administration tasks. When used correctly with proper security practices, it provides powerful capabilities for process management and system integration.

For parallel Python code execution, use `multiprocessing`.
For concurrent I/O operations, use `threading` or `asyncio`.
For external program execution, use `subprocess`.
