"""
Module: Multi-threading for IO-Bound Tasks

Key Insights:
1. Use threads for IO-bound work (network, disk, UI).
2. 'threading.Lock': Standard mutex.
3. Thread Safety: Built-in collections like 'deque' are thread-safe; 'list'/'dict' are mostly safe but rely on atomicity of bytecode which is risky.
"""

import threading
import time
import requests

# 1. Threading for IO (Fetching URLs)
def fetch_url(url):
    print(f"Fetching {url}...")
    resp = requests.get(url)
    print(f"Done {url}: {len(resp.text)} bytes")

urls = ["https://google.com", "https://python.org", "https://github.com"]

threads = []
for url in urls:
    t = threading.Thread(target=fetch_url, args=(url,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# 2. Synchronization (Locks)
class ThreadSafeCounter:
    def __init__(self):
        self.value = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:  # RAII-style lock (Context Manager)
            self.value += 1

counter = ThreadSafeCounter()

def worker():
    for _ in range(1000):
        counter.increment()

workers = [threading.Thread(target=worker) for _ in range(10)]
for w in workers: w.start()
for w in workers: w.join()

print(f"Final Counter Value: {counter.value}")

# 3. ThreadPoolExecutor (Modern way)
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    executor.map(fetch_url, urls)

if __name__ == "__main__":
    pass
