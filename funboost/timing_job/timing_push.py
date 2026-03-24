from funboost.utils import redis_manager
from funboost.core.booster import BoostersManager, Booster

from apscheduler.jobstores.redis import RedisJobStore
from funboost.timing_job.timing_job_base import funboost_aps_scheduler, undefined
from funboost.timing_job.apscheduler_use_redis_store import FunboostBackgroundSchedulerProcessJobsWithinRedisLock
from funboost.funboost_config_deafult import FunboostCommonConfig
from apscheduler.schedulers.base import BaseScheduler
from funboost.constant import RedisKeys

class ApsJobAdder:
    """
    Unified way to add scheduled tasks, added on 2025-01-16. This approach is recommended.
    Users no longer need to worry about which apscheduler object to use for adding scheduled tasks.

    For example, if add_numbers is a consumer function decorated with @boost:
    ApsJobAdder(add_numbers, job_store_kind='memory').add_push_job(
        args=(1, 2),
        trigger='date',  # Use date trigger
        run_date='2025-01-16 18:23:50',  # Set run time
        # id='add_numbers_job'  # Task ID
    )
    """

    queue__redis_aps_map = {}

    def __init__(self, booster: Booster, job_store_kind: str = 'memory',is_auto_start=True,is_auto_paused=False):
        """
        Initialize the ApsJobAdder.

        :param booster: A Booster object representing the function to be scheduled.
        :param job_store_kind: The type of job store to use. Default is 'memory'.
                               Can be 'memory' or 'redis'.
        :param is_auto_start: Whether to automatically start the scheduler on instantiation. Always ensure this is True.
                              If False, even basic CRUD operations on scheduled tasks won't work, let alone running them.
        :param is_auto_paused: Whether to automatically pause the scheduler on instantiation. You can choose as needed.
                               If you only want to perform CRUD on schedules without actually executing task functions,
                               set this to True to pause the scheduler's function execution.

        apscheduler's .start() and pause() have two independent meanings - don't assume they are antonyms of the same operation.
        The opposite of pause is resume, and the prerequisite is that apscheduler.start() has been called first.
        These are native apscheduler concepts that users should learn beforehand.
        """
        self.booster = booster
        self.job_store_kind = job_store_kind
        if getattr(self.aps_obj, 'has_started_flag', False) is False:
            if is_auto_start:
                self.aps_obj.has_started_flag = True
                self.aps_obj.start(paused=is_auto_paused)



    @classmethod
    def get_funboost_redis_apscheduler(cls, queue_name):
        """
        Each queue name's scheduled tasks have their own separate apscheduler timer.
        Each timer uses different Redis jobstore jobs_key and run_times_key to prevent mutual interference
        and retrieving tasks that don't belong to it.
        If all functions share the same timer and jobs_key, when a user only wants to run f1's scheduled task
        and deletes f2 or doesn't need f2's scheduled task, it would cause errors or inconvenience.
        """
        if queue_name in cls.queue__redis_aps_map:
            return cls.queue__redis_aps_map[queue_name]
        redis_jobstores = {

            "default": RedisJobStore(**redis_manager.get_redis_conn_kwargs(),
                                    jobs_key=RedisKeys.gen_funboost_redis_apscheduler_jobs_key_by_queue_name(queue_name),
                                    run_times_key=RedisKeys.gen_funboost_redis_apscheduler_run_times_key_by_queue_name(queue_name),
                                     )
        }
        redis_aps = FunboostBackgroundSchedulerProcessJobsWithinRedisLock(timezone=FunboostCommonConfig.TIMEZONE,
                                                                          daemon=False, jobstores=redis_jobstores)
        redis_aps.set_process_jobs_redis_lock_key(RedisKeys.gen_funboost_apscheduler_redis_lock_key_by_queue_name(queue_name))
        cls.queue__redis_aps_map[queue_name] = redis_aps
        return redis_aps

    @property
    def aps_obj(self) -> BaseScheduler:
        return self.get_aps_obj(self.booster.queue_name,self.job_store_kind)

    @classmethod
    def get_aps_obj(cls,queue_name,job_store_kind):
        if job_store_kind == 'redis':
            return cls.get_funboost_redis_apscheduler(queue_name)
        elif job_store_kind == 'memory':
            return funboost_aps_scheduler
        else:
            raise ValueError('Unsupported job_store_kind')


    def add_push_job(self, trigger=None, args=None, kwargs=None,
                     id=None, name=None,
                     misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                     next_run_time=undefined, jobstore='default', executor='default',
                     replace_existing=False, **trigger_args, ):
        """
        1. The parameters here are the same as apscheduler's add_job parameters - the funboost author did not create new parameters.
        However, the official apscheduler's first parameter is the function itself.
        funboost's ApsJobAdder.add_push_job removes the function parameter because it's passed during class instantiation,
        so there's no need to bother the user again.

        2. add_push_job's purpose is to periodically run consumer_function.push to publish messages to the consumption queue,
        NOT to directly run the consumer function itself on schedule.

        It's equivalent to aps_obj.add_job(consumer_function.push, trigger, args, kwargs, id, name, .....)
        So why not directly use aps_obj.add_job(consumer_function.push, ...)? Because consumer_function.push is an instance method.
        If Redis is used as the jobstore, consumer_function.push will error because instance methods cannot be serialized.
        Only regular functions and static methods can be serialized.
        So add_push_job was developed, which internally uses add_job with push_fun_params_to_broker (a regular function)
        as the first parameter. This function then calls consumer_function.push, effectively working around
        the serialization issue of aps_obj.add_job(consumer_function.push).

        3. Users can also define their own regular function my_push that internally calls consumer_function.push,
        then use aps_obj.add_job with their my_push as the first parameter.
        This approach is easier to understand and identical to apscheduler's native usage.
        But it's less convenient than add_push_job because you need to define a separate my_push function for each consumer function.
        """

        # if not getattr(self.aps_obj, 'has_started_flag', False):
        #     self.aps_obj.has_started_flag = True
        #     self.aps_obj.start(paused=False)
        return self.aps_obj.add_push_job(self.booster, trigger, args, kwargs, id, name,
                                         misfire_grace_time, coalesce, max_instances,
                                         next_run_time, jobstore, executor,
                                         replace_existing, **trigger_args, )


if __name__ == '__main__':
    """
    After 2025, the recommended way to add scheduled tasks is using ApsJobAdder.
    Users no longer need to manually choose which apscheduler object to use for adding scheduled tasks,
    especially when using Redis as jobstores - you can see this from the source code.
    """
    from funboost import boost, BrokerEnum, ctrl_c_recv, BoosterParams, ApsJobAdder


    # Define task processing function
    @BoosterParams(queue_name='sum_queue3', broker_kind=BrokerEnum.REDIS)
    def sum_two_numbers(x, y):
        result = x + y
        print(f'The sum of {x} and {y} is {result}')

    # Start consumer
    # sum_two_numbers.consume()

    # Publish tasks
    sum_two_numbers.push(3, 5)
    sum_two_numbers.push(10, 20)



    # Use ApsJobAdder to add scheduled tasks. The scheduling syntax inside is the same as apscheduler's - users need to be familiar with the well-known apscheduler framework's add_job scheduling parameters.

    # Method 1: Execute once at a specified date
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='date',
        run_date='2025-01-17 23:25:40',
        args=(7, 8),
        id='date_job1'
    )

    # Method 2: Execute at fixed intervals
    ApsJobAdder(sum_two_numbers, job_store_kind='memory').add_push_job(
        trigger='interval',
        seconds=5,
        args=(4, 6),
        id='interval_job1'
    )

    # Method 3: Periodic execution using cron expression
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='cron',
        day_of_week='*',
        hour=23,
        minute=49,
        second=50,
        kwargs={"x": 50, "y": 60},
        replace_existing=True,
        id='cron_job1')
    


    # ctrl_c_recv() # When using a scheduler with daemon threads, you must prevent the main thread from exiting. You can add ctrl_c_recv() at the end of your code or add while 1:time.sleep(10)
