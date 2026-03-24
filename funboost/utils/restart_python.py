import datetime
import os
import sys
import threading
import time

import nb_log

# print(sys.path)

logger = nb_log.get_logger('restart_program')

""" This can only test restart functionality in Windows cmd or Linux.
   You cannot verify restart by checking prints in PyCharm, because after restart the Python process changes and PyCharm console cannot capture output from the new process. So do not run in PyCharm to verify restart functionality.

"""


def restart_program(seconds):
    '''
    Restart the script after n seconds.
    :param seconds:
    :return:
    '''
    """
    This can only test restart functionality in Windows cmd or Linux.
    You cannot verify restart by checking prints in PyCharm, because after restart the Python process changes and PyCharm console cannot capture output from the new process.
    """

    def _restart_program():
        time.sleep(seconds)
        python = sys.executable
        logger.warning(f'Restarting current Python program {python} , {sys.argv}')
        os.execl(python, python, *sys.argv)

    threading.Thread(target=_restart_program).start()


def _run():
    print(datetime.datetime.now(),'Starting program')
    for i in range(1000):
        time.sleep(0.5)
        print(datetime.datetime.now(),i)

if __name__ == '__main__':
    restart_program(10)  # Restart every 10 seconds.
    _run()
