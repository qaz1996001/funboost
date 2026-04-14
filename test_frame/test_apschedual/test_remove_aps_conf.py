
from funboost.timing_job.apscheduler_use_redis_store import funboost_background_scheduler_redis_store
from test_frame.test_apschedual.test_aps_redis_store import consume_func

"""
This file tests modifying scheduled task configuration. When one script starts with a certain scheduled task configuration,
the other script's configuration will automatically change, because the scheduled task configuration is stored and notified via middleware.
"""

funboost_background_scheduler_redis_store.remove_all_jobs()

funboost_background_scheduler_redis_store.add_push_job(consume_func,  # You can also use the my_push function here, which avoids passing the function's location and name. See test_aps_redis_store.py.
                                                       'interval', id='15', name='namexx', seconds=4,
                                                       kwargs={"x": 19, "y": 33},
                                                       replace_existing=True)   # replace_existing means if id already exists, modify it; otherwise add it.



