import time
import json
from funboost import boost, BrokerEnum, BoosterParams, FunctionResultStatus,AsyncResult


@boost(BoosterParams(
    queue_name='test_grpc_queue', broker_kind=BrokerEnum.GRPC,
    broker_exclusive_config={'port': 55051, 'host': '127.0.0.1'},
    is_using_rpc_mode=True,  # When brpc is used as a broker, is_using_rpc_mode can be False; using $booster.publisher.sync_call does not depend on redis for rpc
))
def f(x, y):
    time.sleep(2)
    print(f'x: {x}, y: {y}')
    return x + y


@boost(BoosterParams(
    queue_name='test_grpc_queue2', broker_kind=BrokerEnum.GRPC,
    broker_exclusive_config={'port': 55052, 'host': '127.0.0.1'},
    rpc_timeout=6,
    is_using_rpc_mode=False,  # When brpc is used as a broker, is_using_rpc_mode can be False; if using $booster.publisher.sync_call, it does not depend on redis for rpc
    concurrent_num=500,
))
def f2(a, b):
    time.sleep(5)
    print(f'a: {a}, b: {b}')
    return a * b


if __name__ == '__main__':
    f.consume()
    f2.consume()

    for i in range(100):
       

        """
        sync_call blocks until a result is returned; it will always block regardless of whether you further access rpc_data1.result.
        """
        rpc_data1: FunctionResultStatus = f.publisher.sync_call({'x': i, 'y': i * 2})
        print('grpc f result is :', rpc_data1.result)

        """
        You can still use booster.push, but AsyncResult requires redis as rpc to get the result.
        If you don't further call async_result.result to get the result, f.push will not block.
        """
        async_result :AsyncResult = f.push(i, i * 2)
        print("result from redis:",async_result.result)

        rpc_data2 :FunctionResultStatus = f2.publisher.sync_call({'a': i, 'b': i * 2})
        print('grpc f2 result is :', rpc_data2.result)
