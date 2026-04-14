"""
Demonstrates how to prioritize certain functions over others.
For example, in a web crawler, if you want depth-first traversal, prioritize the detail page crawler function by giving it a higher priority.
If you want breadth-first traversal, prioritize the list page crawler function by giving it a higher priority.

The following code sets f3's priority to 3, f2's priority to 2, and f1's priority to 1.
So after publishing 3000 messages to the queue, f3 will run first and f1 will run last.
Priority applies to a single queue, not across different queues.
However, with a clever approach like the dispatch_fun function below that routes calls to different functions,
you can still implement priority ordering across multiple functions.

Running this, you will see f3 printed first in the console, and f1 printed last.
"""
from funboost import boost, TaskOptions, BrokerEnum


def f1(x, y):
    print(f'f1  x:{x},y:{y}')


def f2(a):
    print(f'f2  a:{a}')


def f3(b):
    print(f'f3  b:{b}')


@boost('test_priority_between_funs', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, qps=100, broker_exclusive_config={'x-max-priority': 5})
def dispatch_fun(fun_name: str, fun_kwargs: dict, ):
    function = globals()[fun_name]
    return function(**fun_kwargs)


if __name__ == '__main__':
    dispatch_fun.clear()
    for i in range(1000):
        dispatch_fun.publish({'fun_name': 'f1', 'fun_kwargs': {'x': i, 'y': i}, },
                             task_options=TaskOptions(other_extra_params={'priroty': 1}))
        dispatch_fun.publish({'fun_name': 'f2', 'fun_kwargs': {'a': i, }, },
                             task_options=TaskOptions(other_extra_params={'priroty': 2}))
        dispatch_fun.publish({'fun_name': 'f3', 'fun_kwargs': {'b': i, }, },
                             task_options=TaskOptions(other_extra_params={'priroty': 3}))

    print(dispatch_fun.get_message_count())
    dispatch_fun.consume()
