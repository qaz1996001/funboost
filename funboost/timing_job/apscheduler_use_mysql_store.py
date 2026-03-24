from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore


from funboost.timing_job import FsdfBackgroundScheduler


"""
This uses MySQL as the persistent store for scheduled tasks, supporting dynamic modification and addition of scheduled tasks.
Users can fully implement this themselves following the code in funboost/timing_job/apscheduler_use_redis_store.py,
since apscheduler supports SQLAlchemyJobStore. It's just changing the jobstores type for the scheduler,
which is entirely apscheduler knowledge and has nothing to do with funboost.
"""