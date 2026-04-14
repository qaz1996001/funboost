from apscheduler.jobstores.redis import RedisJobStore
from funboost.utils.redis_manager import RedisMixin,get_redis_conn_kwargs

from funboost.timing_job import FunboostBackgroundScheduler
from funboost.funboost_config_deafult import BrokerConnConfig, FunboostCommonConfig
from funboost.utils.decorators import RedisDistributedBlockLockContextManager
from funboost.core.loggers import flogger

"""
This uses Redis as the persistent store for scheduled tasks, supporting cross-machine and cross-process,
remotely dynamic modification/addition/deletion of scheduled tasks
"""


class FunboostBackgroundSchedulerProcessJobsWithinRedisLock(FunboostBackgroundScheduler):
    """
    When distributed or multiple processes all start an apscheduler instance using the same database-type jobstores,
    _process_jobs has a high probability of causing errors because _process_jobs uses a thread lock,
    which cannot manage other processes and distributed machines.

    https://groups.google.com/g/apscheduler/c/Gjc_JQMPePc also mentions this bug

    Inheriting Custom schedulers https://apscheduler.readthedocs.io/en/3.x/extending.html allows overriding _create_lock
    """

    process_jobs_redis_lock_key = None

    def set_process_jobs_redis_lock_key(self, lock_key):
        self.process_jobs_redis_lock_key = lock_key
        return self

    # def  _create_lock(self):
    #     return RedisDistributedBlockLockContextManager(RedisMixin().redis_db_frame,self.process_jobs_redis_lock_key,) This class pattern is not suitable for a fixed singleton,
    #     RedisDistributedBlockLockContextManager's pattern is not suitable for always using one object, so it's placed inside def _process_jobs to run

    # def _process_jobs(self):
    #     for i in range(10) :
    #         with RedisDistributedLockContextManager(RedisMixin().redis_db_frame, self.process_jobs_redis_lock_key, ) as lock:
    #             if lock.has_aquire_lock:
    #                 wait_seconds = super()._process_jobs()
    #                 return wait_seconds
    #             else:
    #                 time.sleep(0.1)
    #     return 0.1

    def _process_jobs(self):
        """
        Funboost's approach is to lock at the task retrieval stage, fundamentally preventing duplicate execution.
        This is critical - it prevents multiple apscheduler instances from scanning and retrieving the same
        scheduled task simultaneously, which would indirectly cause duplicate execution.
        In apscheduler 3.xx, this approach prevents the problem of multiple apscheduler instances
        executing scheduled tasks repeatedly - a brilliant solution.

        _process_jobs' function is to scan and retrieve scheduled tasks that need to run,
        not to directly run them. As long as scanning doesn't retrieve the same task twice,
        it indirectly ensures the same scheduled task cannot be executed repeatedly.

        Don't assume that simply adding a Redis distributed lock to your consumer function will prevent
        duplicate task execution. Redis distributed locks prevent the same code block from concurrent execution,
        not from repeated execution. Funboost's brilliant approach is adding the distributed lock to _process_jobs.
        _process_jobs retrieves a batch of scheduled tasks about to run, scanning and deleting them.
        So adding a distributed lock here indirectly prevents duplicate scheduled task execution -
        once a task is retrieved, it's deleted from the jobstore, so other instances can no longer get it.
        """
        if self.process_jobs_redis_lock_key is None:
            raise ValueError('process_jobs_redis_lock_key is not set')
        try:    
            with RedisDistributedBlockLockContextManager(RedisMixin().redis_db_frame, self.process_jobs_redis_lock_key, ):
                return super()._process_jobs()
        except Exception as e:
             # Errors must be caught here, otherwise if RedisDistributedBlockLockContextManager encounters a rare Redis disconnection error, the _main_loop loop would exit, causing the scheduler's task scanning while-loop thread to stop running permanently.
            flogger.exception(f'FunboostBackgroundSchedulerProcessJobsWithinRedisLock _process_jobs error: {e}')
            return 0.1


jobstores = {
    "default": RedisJobStore(**get_redis_conn_kwargs(),
                             jobs_key='funboost.apscheduler.jobs',run_times_key="funboost.apscheduler.run_times")
}

"""
It is recommended not to use this funboost_background_scheduler_redis_store object directly, but instead use ApsJobAdder
to add scheduled tasks, which automatically creates multiple apscheduler object instances.
Especially when using Redis as jobstores, it uses different jobstores with separate jobs_key and run_times_key
for each consumer function.
"""
funboost_background_scheduler_redis_store = FunboostBackgroundSchedulerProcessJobsWithinRedisLock(timezone=FunboostCommonConfig.TIMEZONE, daemon=False, jobstores=jobstores)






"""
Examples of dynamically modifying scheduled task configuration across Python interpreters and machines can be found in:

test_frame/test_apschedual/test_aps_redis_store.py
test_frame/test_apschedual/test_change_aps_conf.py
"""
