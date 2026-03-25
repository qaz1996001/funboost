
from funboost.timing_job.apscheduler_use_redis_store import funboost_background_scheduler_redis_store
from test_frame.test_apschedual.test_aps_redis_store import consume_func

"""
This file tests modifying scheduled task configuration. When one script starts with a certain scheduled task configuration,
the other script's configuration will automatically change, because the scheduled task configuration is stored and notified via middleware.
"""

# Must call .start to modify or add scheduled tasks. To only modify config without executing functions, set paused=True
funboost_background_scheduler_redis_store.start(paused=True) # This script demonstrates remote dynamic modification: dynamically add or delete scheduled task config without executing them. Note paused=True

# View all scheduled task configurations in the database
print(funboost_background_scheduler_redis_store.get_jobs())

#  Delete all scheduled task configurations already added in the database
# funboost_background_scheduler_redis_store.remove_all_jobs()

# Delete the scheduled task with id='691' from the database
# funboost_background_scheduler_redis_store.remove_job(job_id='691')

# Add or modify scheduled task configuration. replace_existing=True means if id already exists, modify it; otherwise add it.
funboost_background_scheduler_redis_store.add_push_job(consume_func,
                                                       'interval', id='15', name='namexx', seconds=4,
                                                       kwargs={"x": 19, "y": 33},
                                                       replace_existing=True)




