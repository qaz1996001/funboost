

import asyncio
import logging
from aiocache import cached, Cache
from aiocache.serializers import JsonSerializer

# Configure logging for easy viewing of output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- Memory cache example --------------------
@cached(
    cache=Cache.MEMORY,          # Use memory backend
    ttl=10,                       # Cache time-to-live 10 seconds
    namespace="memory_add"        # Namespace to avoid key conflicts
)
async def add_memory(x: int, y: int) -> int:
    """Simulate time-consuming computation of the sum of two numbers (memory cache version)"""
    logger.info(f"Computing {x} + {y} ...")
    await asyncio.sleep(2)        # Simulate time-consuming operation (e.g., complex computation)
    return x + y

# -------------------- Redis cache example --------------------
@cached(
    cache=Cache.REDIS,            # Use Redis backend
    endpoint="127.0.0.1",         # Redis address
    port=6379,                     # Redis port
    password=None,                 # Fill in if there is a password
    ttl=30,                         # Cache time-to-live 30 seconds
    serializer=JsonSerializer(),    # Use JSON serialization (easy to read)
    namespace="redis_add"           # Namespace
)
async def add_redis(x: int, y: int) -> int:
    """Simulate time-consuming computation of the sum of two numbers (Redis cache version)"""
    logger.info(f"Computing {x} + {y} ...")
    await asyncio.sleep(2)
    return x + y

# -------------------- Main test function --------------------
async def main():
    # Test memory cache
    logger.info("=== Testing memory cache ===")
    print(await add_memory(3, 5))   # First call, executes computation, caches result
    print(await add_memory(3, 5))   # Second call, returns cached result directly, function body not executed
    print(await add_memory(7, 2))   # Different parameters, recomputes and caches

    logger.info("Waiting 10 seconds for memory cache to expire...")
    await asyncio.sleep(10)          # Wait for memory cache to expire (ttl=10)
    print(await add_memory(3, 5))   # Cache expired, recomputes

    # Test Redis cache
    logger.info("\n=== Testing Redis cache ===")
    try:
        print(await add_redis(10, 20))
        print(await add_redis(10, 20))   # Redis cache hit
        print(await add_redis(5, 5))      # New parameters
    except ConnectionError as e:
        logger.error(f"Redis connection failed, please ensure Redis is running: {e}")

    # Important: close Redis connection pool (should be called on shutdown in persistent applications)
    # Can be omitted here since the script is about to end, but needs management in long-running applications

if __name__ == "__main__":
    asyncio.run(main())
