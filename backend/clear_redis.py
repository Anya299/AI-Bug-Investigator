from redis_client import redis_client

keys = redis_client.keys("rate_limit:*")

print("Found keys:", keys)

for key in keys:
    redis_client.delete(key)

print("Rate limit keys cleared ✅")