import redis
from rq import Queue


redis_connection = redis.Redis(
    host="localhost",
    port=6379,
    db=0
)


evaluation_queue = Queue(
    "ragas",
    connection=redis_connection
)