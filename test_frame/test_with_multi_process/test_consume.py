import time
from auto_run_on_remote import run_current_script_on_remote

run_current_script_on_remote()
from funboost import boost, BrokerEnum, TaskOptions,FunctionResultStatusPersistanceConfig,BoosterParams

"""
Demonstrates launching consumers with multiple processes.
Multi-process and asyncio/threading/gevent/eventlet are cumulative relationships, not parallel.
"""


# qps=5, is_using_distributed_frequency_control=True: distributed rate control, executes 5 times per second globally.
# If is_using_distributed_frequency_control is not set to True, each process will execute 5 times per second independently.
@boost(BoosterParams(queue_name='test_queue_s23', qps=1, broker_kind=BrokerEnum.REDIS,

       ))
def ff(x, y):
    import os
    time.sleep(2)
    print(os.getpid(), x, y)


if __name__ == '__main__':
    # ff.publish()
    ff.clear()


        # This is more complex publishing compared to push; the first argument is the function's parameter dict,
        # and subsequent arguments are task control parameters, such as task_id, delayed task, and rpc mode.
        # ff.publish({'x': i * 10, 'y': i * 20}, )

    # ff(666, 888)  # Run the function directly
    # ff.start()  # Equivalent to consume()
    # ff.consume()  # Equivalent to start()
    # # run_consumer_with_multi_process(ff, 2)  # Start two processes
    # ff.multi_process_consume(3)
    for i in range(1000):
        ff.push(i, y=0)
    ff.multi_process_consume(3)  # Start two processes; equivalent to run_consumer_with_multi_process above; multi_process_start is the new method name.
    # IdeAutoCompleteHelper(ff).multi_process_start(3)  # IdeAutoCompleteHelper provides auto-complete hints, but since the decorator now includes type annotations, ff. already auto-completes in PyCharm.

    time.sleep(100000)
