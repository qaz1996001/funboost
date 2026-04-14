import os
import sys
import time
import signal


def signal_handler(signum, frame):
    print(f'Received signal {signum}, program preparing to exit', flush=True)
    sys.exit(4)
    os._exit(44)



def ctrl_c_recv(confirmation_count=1):
    """
    Adding ctrl_c_recv() at the end of the program mainly keeps the main thread running,
    allowing you to press Ctrl+C on the keyboard to stop the program.
    Even without ctrl_c_recv() at the end, the funboost consumer program will continue running
    permanently, and the console will keep printing logs and `print` output.


    For detailed differences between adding and not adding it, see tutorial section 6.25b.


    You can also skip ctrl_c_recv() and simply add the following at the end of your startup script:
    while 1:
        time.sleep(100)
    to keep the main thread running.
    """
    # signal.signal(signal.SIGTERM, signal_handler)
    
    for i in range(confirmation_count):
        while 1:
            try:
                time.sleep(2)
            except (KeyboardInterrupt,) as e:
                # time.sleep(2)
                print(f'{type(e)} You pressed Ctrl+C, program exiting, attempt {i + 1}', flush=True)
                # time.sleep(2)
                break
    # sys.exit(4)
    os._exit(44)
    # exit(444)
