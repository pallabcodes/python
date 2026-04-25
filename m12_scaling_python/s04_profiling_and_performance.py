"""
Module: Production Diagnostics and Performance Profiling

Key Insights:
1. Don't optimize until you MEASURE.
2. cProfile: Built-in deterministic profiling.
3. tracemalloc: Identifying memory growth and leaks.
4. py-spy: Sampling profiler (can attach to RUNNING processes without restart).
"""

import cProfile
import pstats
import io
import time
import tracemalloc

# 1. CPU Profiling with cProfile
def expensive_calculation():
    total = 0
    for i in range(10**6):
        total += i
    time.sleep(0.1)
    return total

pr = cProfile.Profile()
pr.enable()

expensive_calculation()

pr.disable()
s = io.StringIO()
sortby = pstats.SortKey.CUMULATIVE
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats(10)
# print(s.getvalue())

# 2. Memory Profiling with tracemalloc
tracemalloc.start()

# Simulated memory leak
leak = []
for i in range(1000):
    leak.append("A" * 1000)

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("[ Top 3 Memory Consumers ]")
for stat in top_stats[:3]:
    print(stat)

# 3. Discord/Google Tooling (Reference)
# - py-spy: 'py-spy record -o profile.svg --pid 1234'
# - viztracer: Detailed timeline of execution.
# - scalene: Profiles CPU, Memory, and GPU with AI-driven advice.

# 4. The "Dictionary Penalty" at Scale
# Regular dicts have overhead. Reviewing m02/s07_slots.py is crucial
# when scaling to millions of objects.

if __name__ == "__main__":
    pass
