import nb_log

nb_log.get_logger('ray')
# Import ray and initialize the execution environment
import ray
ray.init(address="127.0.0.1:6379")

# Define a ray remote function
@ray.remote
def hello():
    return "Hello world !"

# Execute the remote function asynchronously; returns a result ID
object_id = hello.remote()

# Synchronously retrieve the computation result
hello = ray.get(object_id)

# Output the computation result
print(hello)
