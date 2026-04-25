"""
Module: Production Hardening — Python in Infrastructure

Focus:
1. CPU CFS Throttling: The 'Silent Killer' in Kubernetes.
2. Signal Handling: Graceful shutdowns in Distributed Systems.
3. Health Check Anti-patterns: Avoiding 'Zombie' processes.
"""
import signal
import time
import sys

def graceful_shutdown_demo():
    print("=== Graceful Shutdown & Signals ===")
    
    def handler(signum, frame):
        print(f"\nReceived signal {signum}. Closing database connections...")
        # L7 Tip: Always use a timeout for graceful shutdowns.
        time.sleep(1)
        print("Shutdown complete.")
        sys.exit(0)
    
    # Register SIGTERM (K8s termination signal)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    
    print("Process running... (Press Ctrl+C to simulate SIGINT/SIGTERM)")
    # time.sleep(2) # Simulate work

def cfs_throttling_explanation():
    """
    ### The CFS Throttling Problem (L7 Engineering Context)
    
    In Kubernetes, you set CPU 'limits'. 
    - If you set `cpu: 500m`, the OS gives you 50ms of CPU time every 100ms.
    - If your Python process holds the GIL for 60ms, the OS 'throttles' the process.
    - Result: High tail latency (p99) even if CPU usage looks low.
    
    **Solution**: 
    1. Align switch interval (`sys.setswitchinterval`) with CFS periods.
    2. Prefer CPU 'requests' over 'limits' for latency-sensitive Python apps.
    """
    print("\n=== K8s / Infrastructure Insights ===")
    print("Current sys.getswitchinterval():", sys.getswitchinterval())
    print("Recommendation: For low-latency microservices, tune the GIL interval to 0.001 (1ms).")

if __name__ == "__main__":
    cfs_throttling_explanation()
    graceful_shutdown_demo()
