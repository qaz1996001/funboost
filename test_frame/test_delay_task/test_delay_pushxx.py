# Must use publish, not push, as explained earlier: to pass parameters beyond the function's own arguments to the broker, use publish.
# Otherwise the framework cannot distinguish function arguments from control parameters. If unclear, think carefully about the relationship between celery's apply_async and delay.
from test_frame.test_delay_task.test_delay_consume import f
import datetime
import time
from funboost import TaskOptions

"""
测试发布延时任务，不是发布后马上就执行函数。

countdown 和 eta 只能设置一个。
countdown 指的是 离发布多少秒后执行，
eta是指定的精确时间运行一次。

misfire_grace_time 是指定消息轮到被消费时候，如果已经超过了应该运行的时间多少秒之内，仍然执行。
misfire_grace_time 如果设置为None，则消息一定会被运行，不会由于大连消息积压导致消费时候已近太晚了而取消运行。
misfire_grace_time 如果不为None，必须是大于等于1的整数，此值表示消息轮到消费时候超过本应该运行的时间的多少秒内仍然执行。
此值的数字设置越小，如果由于消费慢的原因，就有越大概率导致消息被丢弃不运行。如果此值设置为1亿，则几乎不会导致放弃运行(1亿的作用接近于None了)
如果还是不懂这个值的作用，可以百度 apscheduler 包的 misfire_grace_time 概念

"""



f.publish({'x':  45}, task_options=TaskOptions(
    eta=datetime.datetime(2023, 5, 14, 20, 45, 59) + datetime.timedelta(seconds=10)))


    