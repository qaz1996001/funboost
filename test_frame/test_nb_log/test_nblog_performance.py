import time

str1 = ''' 2023-07-05 10:48:35 - lalala - "D:/codes/funboost/test_frame/test_nb_log/log_example.py:15" - <module> - ERROR - pink means the code has errors. pink means the code has errors. pink means the code has errors. pink means the code has errors.'''
import logging
t1 = time.time()
for i in range(10000):
    # print(str1)
    logging.warning(str1)
print(time.time() -t1)