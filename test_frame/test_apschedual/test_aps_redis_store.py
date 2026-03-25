
import apscheduler.jobstores.base
import nb_log
from funboost import boost, BrokerEnum,run_forever
from funboost.timing_job.apscheduler_use_redis_store import funboost_background_scheduler_redis_store

nb_log.get_logger('apscheduler')
'''
test_frame/test_apschedual/test_aps_redis_store.py
Used together with test_frame/test_apschedual/test_change_aps_conf.py for testing dynamic scheduled task modification.

When test_change_aps_conf.py modifies the scheduled task interval and function parameters, test_aps_redis_store.py will automatically update its scheduled task accordingly.
'''

@boost('queue_test_aps_redis', broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE)
def consume_func(x, y):
    print(f'{x} + {y} = {x + y}')


if __name__ == '__main__':
    # funboost_background_scheduler_redis_store.remove_all_jobs() # Delete all configured scheduled tasks from the database
    consume_func.clear()
    #
    funboost_background_scheduler_redis_store.start(paused=False)  # This script demonstrates no-restart dynamic reading of new/deleted scheduled task configs and executing them. Note paused=False
    #
    try:

        funboost_background_scheduler_redis_store.add_push_job(consume_func,  # This is fine. Users define their own function, which can be pickle-serialized and stored in redis, mysql, or mongo. Recommended.
                                                          'interval', id='691', name='namexx', seconds=5,
                                                          kwargs={"x": 7, "y": 8},
                                                          replace_existing=False)
    except apscheduler.jobstores.base.ConflictingIdError as e:
        print('Scheduled task id already exists: {e}')

    consume_func.consume()
    run_forever()






