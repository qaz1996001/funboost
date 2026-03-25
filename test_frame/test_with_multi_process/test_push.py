# from funboost import TaskOptions,IdeAutoCompleteHelper
from test_frame.test_with_multi_process.test_consume import ff

# for i in range(1000, 10000):
#     ff.push(i, y=i * 2)
#
#     # This is more complex publishing compared to push; the first argument is the function's parameter dict,
#     # and subsequent arguments are task control parameters, such as task_id, delayed task, and rpc mode.
#     ff.publish({'x': i * 10, 'y': i * 20}, task_options=TaskOptions(countdown=10, misfire_grace_time=30))
#     ff(6,7)
#     IdeAutoCompleteHelper(ff)(8,9)


ff.push(3001,3002)
