import redis
import os, json


redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
    decode_responses=True
)


def test_redis():

    try:
        redis_client.ping()
        print("Redis connected successfully")
        return True

    except redis.exceptions.ConnectionError:
        print("Redis connection failed")
        return False


def create_cache_key(document_id, question):

    normalized_question = question.strip().lower()

    return f"rag:{document_id}:{normalized_question}"


def get_cached_answer(document_id, question):

    key = create_cache_key(
        document_id,
        question
    )

    cached = redis_client.get(key)

    if cached:
        return json.loads(cached)

    return None


def cache_answer(
    document_id,
    question,
    answer
):

    key = create_cache_key(
        document_id,
        question
    )

    data = {
        "answer": answer
    }

    redis_client.setex(
        key,
        3600,
        json.dumps(data)
    )
    
# --------------------------------------------------
# Save document for a user/session
# --------------------------------------------------

def save_user_document(session_id, document_id):

    key = f"user:{session_id}:documents"

    redis_client.sadd(
        key,
        document_id
    )


# --------------------------------------------------
# Get all documents for a user/session
# --------------------------------------------------

def get_user_documents(session_id):

    key = f"user:{session_id}:documents"

    return list(
        redis_client.smembers(key)
    )

# --------------------------------------------------
# Save chat message
# --------------------------------------------------

def save_chat_message(
    session_id,
    role,
    content
):

    key = f"user:{session_id}:chat"

    message = {
        "role": role,
        "content": content
    }

    redis_client.rpush(
        key,
        json.dumps(message)
    )


# --------------------------------------------------
# Get chat history
# --------------------------------------------------

def get_chat_history(session_id):

    key = f"user:{session_id}:chat"

    messages = redis_client.lrange(
        key,
        0,
        -1
    )

    return [
        json.loads(message)
        for message in messages
    ]
