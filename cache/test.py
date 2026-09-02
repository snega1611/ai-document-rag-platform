from cache.redis_cache import get_user_documents

documents = get_user_documents("test-user-1")

print(documents)