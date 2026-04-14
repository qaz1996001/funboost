# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
import time

from test_frame.best_simple_example.test_consume import f2

f2.clear()

for i in range(100):
    time.sleep(0.1)
    f2.pub({'a': i, 'b': 2 * i})  # pub publishes a dictionary and can also set function control parameters
    f2.push(i*10, i * 20)  # push publishes function arguments directly, not as a dictionary



