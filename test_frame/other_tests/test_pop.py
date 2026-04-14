import time

t1 = time.time()
# import nb_log
print(time.time() -t1)



import gevent
print(time.time() -t1)




import funboost
print(time.time() -t1)

# Get the source file path of the gevent module
# gevent_path = inspect.getfile(gevent)
# print("gevent module path:", gevent_path)
#
# # Get the gevent module import source code
# gevent_source = inspect.getsource(gevent)
# print("gevent module import source code:")
# print(gevent_source)


# import inspect
# import gevent
#
# # Find the specific location where the gevent module is imported
# source_lines, line_num = inspect.findsource(gevent)
# print("gevent module import location:")
# print("File path:", inspect.getfile(gevent))
# print("Line number:", line_num)
# print("Code line content:", source_lines[line_num - 1].strip())

import sys
# print(sys.modules)

