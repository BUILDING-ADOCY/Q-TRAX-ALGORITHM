import os
import sys
import redis
from rq import Queue

"""
task_queue.py

Sets up a reliable RQ queue for Q-TRAX with Redis.
- Uses environment variables for queue name and Redis URL.
- Fails fast if Redis is unavailable.
"""

QUEUE_NAME = os.getenv("QTRAX_QUEUE_NAME", "qtrax_queue")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Redis connection (fail fast on error)
redis_conn = redis.from_url(REDIS_URL) # type: ignore
try:
    redis_conn.ping() # type: ignore
except Exception as e:
    print(f"[RQ] Redis connection failed: {e}")
    sys.exit(1)

# Create RQ queue
qtrax_queue = Queue(QUEUE_NAME, connection=redis_conn)

def get_queue_stats(): # type: ignore
    """Diagnostics: Returns job count and empty status."""
    return {
        "count": qtrax_queue.count,
        "is_empty": qtrax_queue.is_empty()
    } # type: ignore
