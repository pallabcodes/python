"""
Real-world subprocess examples demonstrating practical applications.

This module covers:
- System administration tasks
- Data processing pipelines
- Build and deployment automation
- Monitoring and logging
- Network utilities
- File processing workflows
"""

import subprocess
import json
import time
import os
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path


class RealWorldSubprocessExample:
    """
    Practical subprocess examples for real-world scenarios.
    """

    @staticmethod
    def system_administration() -> None:
        """Demonstrate system administration tasks."""
        print("=== System Administration Tasks ===")

        print("1. Disk usage analysis:")
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split('\n')
            print("   Filesystem usage:")
            for line in lines[:5]:  # Show first 5 lines
                print(f"   {line}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print("   df command not available or failed")

        print("\\n2. Process monitoring:")
        try:
            # Show Python processes
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
            lines = result.stdout.strip().split('\n')
            python_processes = [line for line in lines if 'python' in line.lower()]
            print(f"   Found {len(python_processes)} Python processes:")
            for proc in python_processes[:3]:  # Show first 3
                print(f"   {proc}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print("   ps command not available or failed")

        print("\\n3. Network interface information:")
        try:
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=5)
            # Parse and show interface info
            lines = result.stdout.strip().split('\n')
            interfaces = []
            current_interface = None
            for line in lines:
                if line.startswith('    inet '):
                    if current_interface:
                        interfaces.append(current_interface)
                elif ': ' in line and not line.startswith(' '):
                    current_interface = line.split(':')[1].strip()

            print("   Network interfaces:")
            for iface in interfaces[:3]:  # Show first 3
                print(f"   {iface}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print("   Network commands not available or failed")

    @staticmethod
    def data_processing_pipeline() -> None:
        """Demonstrate data processing pipelines."""
        print("\\n=== Data Processing Pipeline ===")

        # Create sample data
        sample_data = """\
Name,Age,City,Salary
Alice,25,New York,75000
Bob,30,San Francisco,85000
Charlie,35,Chicago,95000
Diana,28,Boston,78000
Eve,32,Seattle,88000
Frank,29,Austin,72000
Grace,31,Denver,81000
Henry,27,Portland,69000
Ivy,33,Miami,92000
Jack,26,Nashville,67000
"""

        print("1. Complete data processing pipeline:")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_data)
            input_file = f.name

        try:
            # Step 1: Filter high earners (>80k)
            p1 = subprocess.Popen(
                ['python3', '-c', '''
import sys, csv
reader = csv.DictReader(sys.stdin)
writer = csv.DictWriter(sys.stdout, fieldnames=reader.fieldnames)
writer.writeheader()
for row in reader:
    if int(row["Salary"]) > 80000:
        writer.writerow(row)
                '''],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True
            )

            # Step 2: Sort by salary descending
            p2 = subprocess.Popen(
                ['sort', '-t,', '-k4,4nr'],  # Sort by 4th column (salary) numeric reverse
                stdin=p1.stdout,
                stdout=subprocess.PIPE,
                text=True
            )
            p1.stdout.close()

            # Step 3: Format output
            p3 = subprocess.Popen(
                ['python3', '-c', '''
import sys, csv
reader = csv.DictReader(sys.stdin)
print("High Earners Report:")
print("=" * 50)
for row in reader:
    print(f"{row['Name']:<10} {row['City']:<15} ${row['Salary']:>8}")
                '''],
                stdin=p2.stdout,
                stdout=subprocess.PIPE,
                text=True
            )
            p2.stdout.close()

            # Send input data and get result
            stdout, stderr = p1.communicate(input=sample_data)
            final_output, _ = p3.communicate()

            print(final_output.decode().strip())

        finally:
            # Cleanup
            os.unlink(input_file)

    @staticmethod
    def build_automation() -> None:
        """Demonstrate build and deployment automation."""
        print("\\n=== Build and Deployment Automation ===")

        print("1. Simulated build process:")

        # Simulate a build pipeline
        build_steps = [
            ("Checking dependencies", ['python3', '-c', 'import sys; print("Python", sys.version)']),
            ("Running tests", ['python3', '-c', 'print("All tests passed!")']),
            ("Building package", ['python3', '-c', 'print("Package built successfully")']),
            ("Running security scan", ['python3', '-c', 'print("Security scan: PASSED")']),
        ]

        for step_name, cmd in build_steps:
            try:
                print(f"   🔄 {step_name}...")
                result = subprocess.run(cmd, capture_output=True, text=True,
                                      timeout=10, check=True)
                print(f"   ✅ {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ {step_name} failed: {e}")
                break
            except subprocess.TimeoutExpired:
                print(f"   ⏱️  {step_name} timed out")
                break
        else:
            print("\\n   🎉 Build pipeline completed successfully!")

        print("\\n2. Deployment simulation:")
        # Simulate deployment with rollback capability
        deployment_script = '''
import time
import random
import sys

print("Starting deployment...")
time.sleep(1)

# Simulate deployment steps
steps = ["Backup current version", "Upload new files", "Update database", "Restart services"]

for step in steps:
    print(f"Executing: {step}")
    time.sleep(0.5)
    
    # Random failure simulation (20% chance)
    if random.random() < 0.2:
        print(f"ERROR: Failed at step '{step}'")
        print("Rolling back...")
        time.sleep(0.5)
        print("Rollback completed")
        sys.exit(1)

print("Deployment completed successfully!")
'''

        try:
            result = subprocess.run(
                ['python3', '-c', deployment_script],
                capture_output=True,
                text=True,
                timeout=15
            )

            print("   Deployment output:")
            for line in result.stdout.strip().split('\\n'):
                print(f"   {line}")

            if result.returncode != 0:
                print(f"   Deployment failed with code: {result.returncode}")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")

        except subprocess.TimeoutExpired:
            print("   Deployment timed out")

    @staticmethod
    def monitoring_and_logging() -> None:
        """Demonstrate monitoring and logging with subprocess."""
        print("\\n=== Monitoring and Logging ===")

        print("1. System resource monitoring:")

        # Monitor system resources
        monitoring_commands = {
            "CPU Usage": ["python3", "-c", """
import psutil
cpu = psutil.cpu_percent(interval=1)
print(f'CPU Usage: {cpu}%')
            """],
            "Memory Usage": ["python3", "-c", """
import psutil
mem = psutil.virtual_memory()
print(f'Memory: {mem.percent}% used ({mem.available//1024//1024}MB free)')
            """],
            "Disk Usage": ["python3", "-c", """
import shutil
total, used, free = shutil.disk_usage('/')
print(f'Disk: {used//1024//1024//1024}GB used, {free//1024//1024//1024}GB free')
            """]
        }

        for metric, cmd in monitoring_commands.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                print(f"   📊 {metric}: {result.stdout.strip()}")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                print(f"   📊 {metric}: Monitoring not available")

        print("\\n2. Log processing pipeline:")
        # Create sample log data
        log_data = """\
2024-01-01 10:00:00 INFO User login: alice
2024-01-01 10:05:00 ERROR Database connection failed
2024-01-01 10:10:00 INFO User login: bob
2024-01-01 10:15:00 WARN High memory usage detected
2024-01-01 10:20:00 ERROR Authentication failed for user: eve
2024-01-01 10:25:00 INFO Backup completed successfully
"""

        # Process logs: extract errors and warnings
        try:
            p1 = subprocess.Popen(
                ['echo', log_data],
                stdout=subprocess.PIPE,
                text=True
            )

            p2 = subprocess.Popen(
                ['grep', 'ERROR\\|WARN'],
                stdin=p1.stdout,
                stdout=subprocess.PIPE,
                text=True
            )
            p1.stdout.close()

            p3 = subprocess.Popen(
                ['python3', '-c', '''
import sys
print("Critical Issues Found:")
print("=" * 30)
count = 0
for line in sys.stdin:
    count += 1
    timestamp, level, message = line.strip().split(' ', 2)
    print(f"{count}. [{level}] {message}")
print(f"\\nTotal critical issues: {count}")
                '''],
                stdin=p2.stdout,
                stdout=subprocess.PIPE,
                text=True
            )
            p2.stdout.close()

            stdout, _ = p3.communicate()
            print(stdout.decode().strip())

        except (subprocess.CalledProcessError, FileNotFoundError):
            print("   Log processing tools not available")

    @staticmethod
    def network_utilities() -> None:
        """Demonstrate network utility operations."""
        print("\\n=== Network Utilities ===")

        print("1. DNS resolution:")
        try:
            result = subprocess.run(['nslookup', 'google.com'],
                                  capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split('\\n')
            for line in lines:
                if 'Address:' in line or 'Name:' in line:
                    print(f"   {line}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print("   DNS lookup not available")

        print("\\n2. Network connectivity test:")
        try:
            result = subprocess.run(['ping', '-c', '3', '-W', '2', '8.8.8.8'],
                                  capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                # Extract ping statistics
                lines = result.stdout.strip().split('\\n')
                for line in lines:
                    if 'packets transmitted' in line or 'avg' in line:
                        print(f"   {line.strip()}")
            else:
                print("   Network connectivity test failed")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print("   Ping utility not available")

        print("\\n3. HTTP request simulation:")
        try:
            # Use curl if available
            result = subprocess.run([
                'curl', '-s', '-I', 'https://httpbin.org/status/200'
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                # Show HTTP headers
                headers = result.stdout.strip().split('\\n')
                print("   HTTP Response Headers:")
                for header in headers[:3]:  # Show first 3 headers
                    if header.strip():
                        print(f"   {header}")
            else:
                print("   HTTP request failed")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print("   curl not available, trying python alternative...")
            # Fallback to python urllib
            try:
                result = subprocess.run([
                    'python3', '-c', '''
import urllib.request
try:
    req = urllib.request.Request("https://httpbin.org/status/200")
    with urllib.request.urlopen(req, timeout=5) as response:
        print(f"HTTP {response.status}: {response.reason}")
        print(f"Content-Type: {response.headers.get(\"content-type\")}")
except Exception as e:
    print(f"HTTP request failed: {e}")
                    '''
                ], capture_output=True, text=True, timeout=10)
                print(f"   {result.stdout.strip()}")
            except subprocess.TimeoutExpired:
                print("   HTTP request timed out")

    @staticmethod
    def file_processing_workflows() -> None:
        """Demonstrate file processing workflows."""
        print("\\n=== File Processing Workflows ===")

        # Create sample files
        sample_files = {
            "data1.txt": "Line 1: Apple\\nLine 2: Banana\\nLine 3: Cherry\\n",
            "data2.txt": "Line 1: Date\\nLine 2: Elderberry\\nLine 3: Fig\\n",
            "data3.txt": "Line 1: Grape\\nLine 2: Honeydew\\nLine 3: Kiwi\\n"
        }

        print("1. Multi-file processing pipeline:")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create sample files
            for filename, content in sample_files.items():
                (temp_path / filename).write_text(content)

            try:
                # Combine all files
                p1 = subprocess.Popen(
                    ['cat'] + [str(temp_path / f) for f in sample_files.keys()],
                    stdout=subprocess.PIPE,
                    text=True
                )

                # Sort lines
                p2 = subprocess.Popen(
                    ['sort'],
                    stdin=p1.stdout,
                    stdout=subprocess.PIPE,
                    text=True
                )
                p1.stdout.close()

                # Count occurrences
                p3 = subprocess.Popen(
                    ['uniq', '-c'],
                    stdin=p2.stdout,
                    stdout=subprocess.PIPE,
                    text=True
                )
                p2.stdout.close()

                # Format output
                p4 = subprocess.Popen(
                    ['python3', '-c', '''
import sys
print("Combined File Analysis:")
print("=" * 30)
for line in sys.stdin:
    count, content = line.strip().split(None, 1)
    print(f"{content}: {count} occurrence(s)")
                    '''],
                    stdin=p3.stdout,
                    stdout=subprocess.PIPE,
                    text=True
                )
                p3.stdout.close()

                stdout, _ = p4.communicate()
                print(stdout.decode().strip())

            except (subprocess.CalledProcessError, FileNotFoundError):
                print("   File processing tools not available")

        print("\\n2. Archive and compression workflow:")
        try:
            # Create a simple archive workflow simulation
            result = subprocess.run([
                'python3', '-c', '''
import tarfile
import io
import sys

# Simulate creating a tar archive in memory
tar_buffer = io.BytesIO()
with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
    # Add some virtual files
    for i in range(3):
        info = tarfile.TarInfo(name=f"file{i}.txt")
        content = f"Content of file {i}\\n".encode()
        info.size = len(content)
        tar.addfile(info, io.BytesIO(content))

print(f"Created tar archive with {len(tar_buffer.getvalue())} bytes")
                '''
            ], capture_output=True, text=True, timeout=10)

            print(f"   {result.stdout.strip()}")

        except subprocess.TimeoutExpired:
            print("   Archive operation timed out")

    @staticmethod
    def devops_automation() -> None:
        """Demonstrate DevOps automation scenarios."""
        print("\\n=== DevOps Automation ===")

        print("1. Docker container management simulation:")

        # Simulate docker-like operations
        container_ops = [
            ("Building image", ['python3', '-c', 'print("FROM ubuntu:latest\\nRUN apt-get update\\nCMD echo hello")']),
            ("Running container", ['python3', '-c', 'print("Container started with ID: abc123")']),
            ("Health check", ['python3', '-c', 'import time; time.sleep(0.5); print("Container healthy")']),
        ]

        for op_name, cmd in container_ops:
            try:
                print(f"   🐳 {op_name}...")
                result = subprocess.run(cmd, capture_output=True, text=True,
                                      timeout=5, check=True)
                print(f"   ✅ {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ {op_name} failed: {e}")
            except subprocess.TimeoutExpired:
                print(f"   ⏱️  {op_name} timed out")

        print("\\n2. CI/CD pipeline simulation:")
        pipeline_steps = {
            "lint": "python3 -m flake8 --version || echo 'flake8 not available'",
            "test": "python3 -c 'import unittest; print(\"Tests passed\")'",
            "build": "python3 -c 'print(\"Package built successfully\")'",
            "deploy": "python3 -c 'print(\"Deployment completed\")'"
        }

        print("   CI/CD Pipeline:")
        print("   " + "=" * 20)

        for step, cmd in pipeline_steps.items():
            try:
                print(f"   🔄 Running {step}...")
                result = subprocess.run(cmd, shell=True, capture_output=True,
                                      text=True, timeout=10, check=True)
                print(f"   ✅ {step}: {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ {step} failed: {e.stderr.strip()}")
                break
        else:
            print("\\n   🎉 CI/CD pipeline completed successfully!")


def main() -> None:
    """Run all real-world examples."""
    print("Real-World Subprocess Examples")
    print("=" * 35)

    example = RealWorldSubprocessExample()

    try:
        example.system_administration()
        example.data_processing_pipeline()
        example.build_automation()
        example.monitoring_and_logging()
        example.network_utilities()
        example.file_processing_workflows()
        example.devops_automation()

        print("\n" + "=" * 35)
        print("All real-world examples completed successfully!")

    except Exception as e:
        print(f"\nExample failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
