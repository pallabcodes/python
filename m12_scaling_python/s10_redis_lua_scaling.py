"""
Module: Redis Scaling and Atomic Lua Scripting
Target: L7 Backend Engineers (Google/Discord Scale)

Key Techniques:
1. Pipelining: Batching commands to reduce network round-trips (Essential for 1M+ ingestion).
2. Atomic Lua Scripts: Executing logic server-side in Redis to avoid race conditions and GIL.
3. 1M Ingestion Lab: Benchmarking high-throughput writes.
"""

import redis
import time
import logging
import asyncio

logger = logging.getLogger(__name__)

# 1. Distributed Rate Limiter in LUA
# This script is sent once to Redis and executed atomically.
# Logic: Token Bucket algorithm.
LUA_RATE_LIMITER = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local interval = tonumber(ARGV[2])

local current = redis.call('get', key)
if current and tonumber(current) >= limit then
    return 0
else
    redis.call('incr', key)
    if not current then
        redis.call('expire', key, interval)
    end
    return 1
end
"""

class RedisEliteScaling:
    def __init__(self, host='localhost', port=6379):
        # Use a connection pool for L7 efficiency
        self.pool = redis.ConnectionPool(host=host, port=port, db=0)
        self.r = redis.Redis(connection_pool=self.pool)
        self._limiter_sha = self.r.script_load(LUA_RATE_LIMITER)

    def benchmark_1m_ingestion(self):
        """
        Ingests 1 Million keys using Pipelining.
        Without pipelining, this would take minutes. With it, seconds.
        """
        logger.info("Starting 1 Million Key Ingestion benchmark...")
        start_time = time.perf_counter()
        
        # Use a pipeline to batch commands
        pipe = self.r.pipeline(transaction=False)
        for i in range(1000000):
            pipe.set(f"key:{i}", f"value:{i}")
            
            # Send in chunks of 10k to prevent OOM on the client/server buffer
            if i % 10000 == 0:
                pipe.execute()
        
        pipe.execute()
        duration = time.perf_counter() - start_time
        logger.info(f"Ingested 1,000,000 keys in {duration:.2f}s ({(1000000/duration):.0f} ops/sec)")

    def check_rate_limit(self, user_id: str):
        """
        Executes the Lua script atomically on the Redis server.
        """
        # evalsha is faster than eval after the first load
        return bool(self.r.evalsha(self._limiter_sha, 1, f"rate:limit:{user_id}", 5, 60))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Note: Requires a running Redis server
    try:
        client = RedisEliteScaling()
        # client.benchmark_1m_ingestion()
        
        # Atomic check
        allowed = client.check_rate_limit("user_123")
        logger.info(f"User 123 allowed: {allowed}")
    except redis.exceptions.ConnectionError:
        logger.warning("Redis server not found. Reference the code for patterns.")
