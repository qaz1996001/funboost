from funcs import fun_sum
from funboost import ApsJobAdder,ctrl_c_recv

if __name__ == '__main__':
    """
    This line ApsJobAdder(fun_sum,job_store_kind='redis',is_auto_paused=False) is very important. The apscheduler timer must be started.
    Even if you don't plan to add scheduled tasks, the apscheduler object still needs to be started.
    If you don't start the apscheduler object, it won't scan and execute the scheduled task plans already added in redis,
    and it won't automatically push messages to the message queue. fun_sum.consume() will have no tasks to execute.
    You'll then be confused asking why the scheduled tasks already added to redis are not being executed.
    """
    ApsJobAdder(fun_sum,job_store_kind='redis',)  # This line of code internally starts the apscheduler object, which will scan scheduled tasks in redis and execute them. The scheduled task's function is to push messages to the message queue.

    fun_sum.consume()  # Start consuming messages from the message queue
    ctrl_c_recv()   # This line is very important. The main thread must be prevented from exiting, otherwise the background apscheduler object will exit and you'll be confused again about why scheduled tasks aren't running. This is apscheduler's own knowledge, so I won't elaborate.