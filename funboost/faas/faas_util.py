
from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter

IS_AUTO_START_APSCHEDULER = True # Must be started; scheduled tasks cannot be retrieved or added without it. Do not change this to False.
IS_AUTO_PAUSED_APSCHEDULER = True # You can pause the scheduler. The web interface is used for CRUD operations on scheduled tasks without triggering sending scheduled tasks to message queues. In the consumer script deployment, booster starts consuming and starts the scheduler without pausing.

def gen_aps_job_adder(queue_name, job_store_kind):
    return SingleQueueConusmerParamsGetter(queue_name).generate_aps_job_adder(
        job_store_kind=job_store_kind, is_auto_start=IS_AUTO_START_APSCHEDULER, is_auto_paused=IS_AUTO_PAUSED_APSCHEDULER)