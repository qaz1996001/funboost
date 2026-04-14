
"""
This script demonstrates that, since the Booster object supports pickle serialization
as of 2025-08, the following syntax is now supported:

  aps_obj_sum_two_numbers2.add_job(
      sum_two_numbers2.push, ...)

This allows users to understand that the essence of scheduled tasks is pushing to a
message queue, not directly executing the function itself.

Users looking at this script mainly need to understand the difference between
add_push_job and add_job.
"""
from funboost import boost, BrokerEnum,ctrl_c_recv,BoosterParams,ApsJobAdder

# Define the task handler function
@boost(BoosterParams(queue_name='sum_queue552', broker_kind=BrokerEnum.REDIS))
def sum_two_numbers2(x, y):
    result = x + y
    print(f'The sum of {x} and {y} is {result}')

if __name__ == '__main__':
    # ApsJobAdder(sum_two_numbers2, job_store_kind='redis').add_push_job(
    #     trigger='interval',
    #     seconds=5,
    #     args=(4, 6),
    #     replace_existing=True,
    #     id='interval_job501',
    # )
    aps_job_adder_sum_two_numbers2 = ApsJobAdder(sum_two_numbers2, job_store_kind='redis',is_auto_paused=False)
    aps_obj_sum_two_numbers2 =aps_job_adder_sum_two_numbers2.aps_obj
    aps_obj_sum_two_numbers2.remove_all_jobs()  # Optional: remove all previously added scheduled tasks for sum_two_numbers2

    # The previously recommended way to add a scheduled task: add_push_job
    aps_job_adder_sum_two_numbers2.add_push_job(
        # ApsJobAdder.add_push_job does not need the first argument func (the job function)
        trigger='interval',
        seconds=5,
        args=(4, 6),
        replace_existing=True,
        id='interval_job503',
    )


    """
    After 2025-08, you can now use the familiar add_job directly, passing $consumer_function.push
    as the first argument func.

    When using a database like Redis (rather than memory) as the apscheduler jobstore,
    apscheduler.add_job needs to pickle-serialize the first argument func.
    sum_two_numbers2.push is an instance method; the Booster object's attribute chain includes
    threading.Lock and socket types, which are not pickle-serializable, so the original approach
    required using ApsJobAdder.add_push_job as a workaround.

    Since Booster now supports pickle serialization and deserialization, sum_two_numbers2.push
    can be used as the job function directly.

    (Note: For those interested, see the __getstate__ and __setstate__ implementation in
    funboost/core/booster.py to understand how pickle support was achieved — it's quite clever.)
    """
    aps_obj_sum_two_numbers2.add_job(
        func = sum_two_numbers2.push,  # aps_obj.add_job is native; it requires the first argument func, i.e., sum_two_numbers2.push
        trigger='interval',
        seconds=5,
        args=(40, 60),
        replace_existing=True,
        id='interval_job504',
    )


    ctrl_c_recv()
