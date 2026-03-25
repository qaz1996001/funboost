# Must use publish, not push: to pass parameters beyond the function's own arguments to the broker, use publish.
# Otherwise the framework cannot distinguish function arguments from control parameters. If unclear, think carefully about the relationship between celery's apply_async and delay.
from test_frame.test_delay_task.test_delay_consume import f
import datetime
import time
from funboost import TaskOptions

"""
Test publishing delayed tasks -- the function is not executed immediately after publishing.

Only one of countdown and eta can be set.
countdown: seconds after publishing before execution.
eta: an exact datetime to run once.

misfire_grace_time specifies, when a message's turn to be consumed arrives, how many seconds
past the scheduled time it will still be executed.
If misfire_grace_time is None, the message will always be run and will not be cancelled due
to large message backlogs causing late consumption.
If not None, it must be an integer >= 1; it represents how many seconds past the scheduled
time a message will still be executed when it is consumed.
The smaller this value, the higher the probability of messages being discarded due to slow
consumption. If set to 100 million, it will almost never lead to abandonment (effectively
the same as None).
If still unclear, search for the apscheduler package's misfire_grace_time concept.
"""
# for i in range(1, 20):
#     time.sleep(1)
#
#     # 消息发布10秒后再执行。如果消费慢导致任务积压，misfire_grace_time为None，即使轮到消息消费时候离发布超过10秒了仍然执行。
#     f.publish({'x': i}, task_options=TaskOptions(countdown=10))
#
#     # 规定消息在17点56分30秒运行，如果消费慢导致任务积压，misfire_grace_time为None，即使轮到消息消费时候已经过了17点56分30秒仍然执行。
#     f.publish({'x': i * 10}, task_options=TaskOptions(
#         eta=datetime.datetime(2023, 5, 14, 17, 56, 30) + datetime.timedelta(seconds=i)))
#
#     # 消息发布10秒后再执行。如果消费慢导致任务积压，misfire_grace_time为30，如果轮到消息消费时候离发布超过40 (10+30) 秒了则放弃执行，
#     # 如果轮到消息消费时候离发布时间是20秒，由于 20 < (10 + 30)，则仍然执行
#     f.publish({'x': i * 100}, task_options=TaskOptions(
#         countdown=10, misfire_grace_time=30))
#
#     # 规定消息在17点56分30秒运行，如果消费慢导致任务积压，如果轮到消息消费时候已经过了17点57分00秒，
#     # misfire_grace_time为30，如果轮到消息消费时候超过了17点57分0秒 则放弃执行，
#     # 如果如果轮到消息消费时候是17点56分50秒则执行。
#     f.publish({'x': i * 1000}, task_options=TaskOptions(
#         eta=datetime.datetime(2023, 5, 14, 17, 56, 30) + datetime.timedelta(seconds=i),
#         misfire_grace_time=30))  # 按指定的时间运行一次。
#
#     # 这个设置了消息由于消息堆积导致运行的时候比本应该运行的时间如果小于1亿秒，就仍然会被执行，所以几乎肯定不会被放弃运行
#     f.publish({'x': i * 10000}, task_options=TaskOptions(
#         eta=datetime.datetime(2022, 5, 19, 17, 56, 30) + datetime.timedelta(seconds=i),
#         misfire_grace_time=100000000))   # 按指定的时间运行一次。

f.publish({'x':  10}, task_options=TaskOptions(
    eta=datetime.datetime.now() + datetime.timedelta(seconds=20)))

f.push(666)
time.sleep(100000)