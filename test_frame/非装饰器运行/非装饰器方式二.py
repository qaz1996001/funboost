from funboost import boost,IdeAutoCompleteHelper,ConcurrentModeEnum


def add(a, b):
    print(a + b)

# The result of deco(a=100)(f)(x=1,y=2) is the same as decorating f with deco(100) and then calling f(x=1,y=2).
# This is the fundamental nature of decorators; no further elaboration needed here.
add_boost = boost('queue_test_f01b',  qps=0.2,concurrent_mode= ConcurrentModeEnum.THREADING)(add)   # type: IdeAutoCompleteHelper
add_boost.consume()

if __name__ == '__main__':
    for i in range(10, 20):
        add_boost.push(a=i, b=i * 2)  # consumer.publisher_of_same_queue.publish  publish a task
    add_boost.consume()  # Start consuming in the current process with multi-thread concurrency
    add_boost.multi_process_consume(2)  # Start 2 separate processes with multi-thread concurrency