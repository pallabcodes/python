import sys
import threading
import time
import collections
import signal
from typing import Dict, List, Optional

class SamplingProfiler:
    """
    True Sampling Profiler (L7 Standard).
    Samples stack frames of all threads at a regular interval.
    Extremely low overhead compared to cProfile.
    """
    def __init__(self, interval=0.01):
        self.interval = interval
        self.samples = collections.defaultdict(int)
        self._active = False
        self._thread = None

    def start(self):
        if self._active:
            return
        self._active = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._active = False
        if self._thread:
            self._thread.join()

    def _run(self):
        while self._active:
            # Sample all threads
            for thread_id, frame in sys._current_frames().items():
                stack = self._format_stack(frame)
                self.samples[stack] += 1
            time.sleep(self.interval)

    def _format_stack(self, frame):
        stack = []
        while frame:
            code = frame.f_code
            stack.append(f"{code.co_filename}:{code.co_name}:{frame.f_lineno}")
            frame = frame.f_back
        return " -> ".join(reversed(stack))

    def get_top_bottlenecks(self, n=5):
        sorted_samples = sorted(self.samples.items(), key=lambda x: x[1], reverse=True)
        total = sum(self.samples.values())
        return [
            {"stack": stack, "percentage": (count / total) * 100}
            for stack, count in sorted_samples[:n]
        ]

# Example Usage context for the engineer
if __name__ == "__main__":
    profiler = SamplingProfiler()
    profiler.start()
    # Run heavy workload
    time.sleep(2)
    profiler.stop()
    for b in profiler.get_top_bottlenecks():
        print(f"{b['percentage']:.1f}% | {b['stack'][-100:]}")
