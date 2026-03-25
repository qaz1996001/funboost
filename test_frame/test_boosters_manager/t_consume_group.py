"""
Demonstrates using BoostersManager.consume_group($booster_group) to start a consumer group.

BoostersManager.consume_group(booster_group=GROUP1_NAME)
is equivalent to internally executing f1.consume() f2.consume() to start consumer functions separately.

Since both f1 and f2 have booster_group set to GROUP1_NAME, they will be started as a consumer group.
"""

import time
from funboost import boost, BoosterParams, BoostersManager, ConcurrentModeEnum
from funboost.utils.ctrl_c_end import ctrl_c_recv


GROUP1_NAME = "my_group1"

# Custom parameter class that inherits BoosterParams, used to reduce repetitive parameters
# across consumer function decorators — no need to repeat the booster_group parameter each time.
class MyGroup1BoosterParams(BoosterParams):
    concurrent_mode: str = ConcurrentModeEnum.SINGLE_THREAD
    booster_group: str = GROUP1_NAME  # Specify the consumer group name


@boost(
    MyGroup1BoosterParams(
         # Using the custom class MyGroup1BoosterParams, so f1's booster_group will automatically be set to GROUP1_NAME
        queue_name="queue_test_consume_gq1",
    )
)
def f1(x):
    time.sleep(2)
    print(f"f1 {x}")


@boost(
    MyGroup1BoosterParams(
        # Using the custom class MyGroup1BoosterParams, so f2's booster_group will automatically be set to GROUP1_NAME
        queue_name="queue_test_consume_gq2",
    )
)
def f2(x):
    time.sleep(2)
    print(f"f2 {x}")


@boost(
    BoosterParams(
        # Not using the custom class MyGroup1BoosterParams, using BoosterParams directly, so f3's booster_group is None
        queue_name="queue_test_consume_gq3",
        concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
    )
)
def f3(x):
    time.sleep(2)
    print(f"f3 {x}")


if __name__ == "__main__":
    for i in range(10):
        f1.push(i)
        f2.push(i)
        f3.push(i)

    # f1.consume() # Start consumer functions one by one; if you find it tedious to start each one individually, use BoostersManager.consume_group to start all functions in a group at once
    # f2.consume()

    BoostersManager.consume_group(
        GROUP1_NAME
    )  # Start consumer group GROUP1_NAME in the current process, equivalent to executing f1.consume() f2.consume() internally
    # BoostersManager.multi_process_consume_group(GROUP1_NAME,2) # Start consumer group with multiple processes
    ctrl_c_recv()
