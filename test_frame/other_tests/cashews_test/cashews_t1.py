from cashews import cache
import time

# Note: Make sure redis is installed in your environment
cache.setup("redis://127.0.0.1:6379")

@cache.callable(ttl="10s", lock=True)
def get_data(name):
    print("--- Executing synchronous query ---")
    time.sleep(2)
    return {"status": 1, "name": name}

if __name__ == "__main__":
    # This calling style is synchronously compatible in many versions
    print(get_data("test"))