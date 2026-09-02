import redis
from rq import Queue

from evaluation.evaluator import evaluate_response


# --------------------------------------------------
# Redis connection
# --------------------------------------------------

redis_connection = redis.Redis(
    host="localhost",
    port=6379,
    db=0
)


# --------------------------------------------------
# Queue
# --------------------------------------------------

evaluation_queue = Queue(
    "ragas",
    connection=redis_connection
)


# --------------------------------------------------
# Add Ragas job
# --------------------------------------------------

job = evaluation_queue.enqueue(
    evaluate_response,
    "What is the eligibility criteria?",
    "The candidate must have a bachelor's degree.",
    "The eligibility criteria is a bachelor's degree."
)


print("=" * 60)
print("RAGAS TEST JOB ADDED")
print("=" * 60)

print("Job ID:", job.id)
print("Status:", job.get_status())