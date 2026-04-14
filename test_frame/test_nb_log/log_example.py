import sys
import time

print('print before importing nb_log is plain')

from nb_log import get_logger

print('print after importing nb_log is an enhanced version with clickable jump-to-source')

logger = get_logger('lalala', log_filename='lalala.log',is_add_elastic_handler=False)

t1 = time.time()
for i in range(100000):
    # logger.debug(f'debug is green, indicating debug info; code is OK. ' * 3)
    # logger.info('info is light blue, normal log. ' * 4)
    # logger.warning('yellow, there is a warning. ' * 4)
    # logger.error('pink means the code has errors. ' * 4)
    # logger.critical('deep red, indicates a critical error occurred. ' * 4)
    print('After importing nb_log once, print in any file in the project is an enhanced version with clickable jump; clicking line numbers in the output console automatically opens the file and jumps to the exact line.')

print(time.time()-t1)


#


