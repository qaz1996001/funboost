import random
import time

from funboost import boost, BoosterParams, fct


@boost(BoosterParams(queue_name='queue_test_fct', qps=2, concurrent_num=5, ))
def f(a, b):
    print(fct.task_id)  # Get the task id of the message
    print(fct.function_result_status.run_times)  # Get how many times the message has been retried
    print(fct.full_msg)  # Get the full message, including values of a and b, publish time, task_id, etc.
    print(fct.function_result_status.publish_time)  # Get the publish time of the message
    print(fct.function_result_status.get_status_dict())  # Get task info as a dict.

    time.sleep(20)
    if random.random() > 0.5:
        raise Exception(f'{a} {b} simulated error')
    print(a + b)
    common_fun()
    return a + b


def common_fun():
    """ common_fun can also automatically know through context what message is being consumed, without needing f to pass taskid and full_msg as arguments to common_fun """
    print(f'common_fun can also automatically know the message taskid without passing taskid as an argument; taskid: {fct.task_id}, full_msg: {fct.full_msg}')


if __name__ == '__main__':
    # f(5, 6)  # 可以直接调用

    for i in range(0, 200):
        f.push(i, b=i * 2)

    f.consume()
