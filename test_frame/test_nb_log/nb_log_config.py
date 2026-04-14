# coding=utf8
"""
This file nb_log_config.py is auto-generated into the root directory of the Python project.
Variables written here will override values in nb_log_config_default. This configures the nb_log package's defaults.
But the final configuration is determined by the parameters passed to get_logger_and_add_handlers;
if the corresponding parameter is None, the values here will be used.
"""

"""
If you are against colored logs, set DEFAULUT_USE_COLOR_HANDLER = False
If you are against block-style background colored logs, set DISPLAY_BACKGROUD_COLOR_IN_CONSOLE = False
If you want to suppress nb_log's tips about how to configure PyCharm colors, set WARNING_PYCHARM_COLOR_SETINGS = False
If you want to change the log template, set the FORMATTER_KIND parameter; 7 templates are included, and you can add custom ones.
LOG_PATH configures the folder path where log files are saved.
"""

# noinspection PyUnresolvedReferences
import logging
import os
# noinspection PyUnresolvedReferences
from pathlib import Path  # noqa
import socket
from pythonjsonlogger.jsonlogger import JsonFormatter


def get_host_ip():
    ip = ''
    host_name = ''
    # noinspection PyBroadException
    try:
        sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sc.connect(('8.8.8.8', 80))
        ip = sc.getsockname()[0]
        host_name = socket.gethostname()
        sc.close()
    except Exception:
        pass
    return ip, host_name


computer_ip, computer_name = get_host_ip()


class JsonFormatterJumpAble(JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        # log_record['jump_click']   = f"""File '{record.__dict__.get('pathname')}', line {record.__dict__.get('lineno')}"""
        log_record[f"{record.__dict__.get('pathname')}:{record.__dict__.get('lineno')}"] = ''  # Add a clickable jump-to-source field.
        log_record['ip'] = computer_ip
        log_record['host_name'] = computer_name
        super().add_fields(log_record, record, message_dict)
        if 'for_segmentation_color' in log_record:
            del log_record['for_segmentation_color']


DING_TALK_TOKEN = '3dd0eexxxxxadab014bd604XXXXXXXXXXXX'  # DingTalk alert robot

EMAIL_HOST = ('smtp.sohu.com', 465)
EMAIL_FROMADDR = 'aaa0509@sohu.com'  # 'matafyhotel-techl@matafy.com',
EMAIL_TOADDRS = ('cccc.cheng@silknets.com', 'yan@dingtalk.com',)
EMAIL_CREDENTIALS = ('aaa0509@sohu.com', 'abcdefg')

ELASTIC_HOST = '127.0.0.1'
ELASTIC_PORT = 9200

KAFKA_BOOTSTRAP_SERVERS = ['192.168.199.202:9092']
ALWAYS_ADD_KAFKA_HANDLER_IN_TEST_ENVIRONENT = False

MONGO_URL = 'mongodb://myUserAdmin:mimamiama@127.0.0.1:27016/admin'

# Whether print in the project is automatically written to a file. None means no redirect. Auto creates one file per day, e.g., 2023-06-30.my_proj.print; file is placed in the defined LOG_PATH.
# If you set the env var, e.g., export PRINT_WRTIE_FILE_NAME="my_proj.print" (Linux temporary env var syntax; for Windows syntax, look it up yourself), then the env var filename takes priority over the one set in nb_log_config.py.
PRINT_WRTIE_FILE_NAME = None  #  Path(sys.path[1]).name + '.print'

# All standard output in the project (including print and streamHandler logs) is written to this file. Auto creates one file per day, e.g., 2023-06-30.my_proj.std; file is placed in the defined LOG_PATH.
# If you set the env var, e.g., export SYS_STD_FILE_NAME="my_proj.std" (Linux temporary env var syntax), then the env var filename takes priority over the one set in nb_log_config.py.
SYS_STD_FILE_NAME =  None # Path(sys.path[1]).name + '.std'

USE_BULK_STDOUT_ON_WINDOWS = True  # Whether to batch stdout every 0.1 seconds on Windows; Windows IO is too slow.

DEFAULUT_USE_COLOR_HANDLER = True  # Whether to use colored logs by default.
DISPLAY_BACKGROUD_COLOR_IN_CONSOLE = False  # Whether to display block-background colored logs in the console. False = no large background color blocks.
AUTO_PATCH_PRINT = True  # Whether to auto-apply monkey patch to print; if patched, print auto-colorizes and is clickable for jump-to-source.
SHOW_PYCHARM_COLOR_SETINGS = True  # Some people dislike the tip shown at startup about how to optimize PyCharm console colors; set to False to suppress it.

DEFAULT_ADD_MULTIPROCESSING_SAFE_ROATING_FILE_HANDLER = False  # Whether to also record logs to a log file by default.
LOG_FILE_SIZE = 100  # Unit is MB; slice size of each log file; auto-rotate after exceeding this size.
LOG_FILE_BACKUP_COUNT = 3  # Default maximum number of backup files per log file; old ones are deleted when exceeded.

LOG_PATH = '/pythonlogs'  # Default log folder; if no drive name is specified, it is under the root directory of the project's disk.
# LOG_PATH = Path(__file__).absolute().parent / Path("pythonlogs")  # This config automatically creates a pythonlogs folder in your project root and writes there.
if os.name == 'posix':  # Non-root Linux users and Mac users cannot access /pythonlogs (no permission), so it defaults to home/[username]. For example, if your Linux username is xiaomin, logs default to /home/xiaomin/pythonlogs.
    home_path = os.environ.get("HOME", '/')  # Gets the current user's home directory on Linux; no manual setting needed.
    LOG_PATH = Path(home_path) / Path('pythonlogs')  # Linux/Mac permissions are strict; non-root cannot write to /pythonlogs; change the default.

LOG_FILE_HANDLER_TYPE = 1  # 1 2 3 4 5
"""
LOG_FILE_HANDLER_TYPE can be set to one of 4 values: 1, 2, 3, 4, 5.
1 = Multiprocess-safe file log with size-based rotation (custom implementation using batch writes to reduce file lock operations).
    Tested with 10 processes writing rapidly: 100x faster than option 5 on Windows, 5x faster on Linux.
2 = Multiprocess-safe file log with daily rotation; one log file per day.
3 = Single file log with no rotation (no rotation = no process-safety issues).
4 = WatchedFileHandler; only works on Linux; relies on logrotate externally for file rotation; multiprocess-safe.
5 = Third-party concurrent_log_handler.ConcurrentRotatingFileHandler for size-based rotation;
    uses file locks for multiprocess-safe rotation; fcntl on Linux performs OK, win32con on Windows is very slow.
    For size-based rotation, choose option 1 over option 5.
"""

LOG_LEVEL_FILTER = logging.DEBUG  # Default log level; logs below this level are not recorded. E.g., set to INFO: logger.debug won't be recorded; only logger.info and above will be.

RUN_ENV = 'test'

FORMATTER_DICT = {
    1: logging.Formatter(
        'Log time [%(asctime)s] - Logger name [%(name)s] - File [%(filename)s] - Line [%(lineno)d] - Level [%(levelname)s] - Message [%(message)s]',
        "%Y-%m-%d %H:%M:%S"),
    2: logging.Formatter(
        '%(asctime)s - %(name)s - %(filename)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s',
        "%Y-%m-%d %H:%M:%S"),
    3: logging.Formatter(
        '%(asctime)s - %(name)s - [  File "%(pathname)s", line %(lineno)d, in %(funcName)s ] - %(levelname)s - %(message)s',
        "%Y-%m-%d %H:%M:%S"),  # A template that mimics traceback exceptions with clickable jump-to-log-location
    4: logging.Formatter(
        '%(asctime)s - %(name)s - "%(filename)s" - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s -               File "%(pathname)s", line %(lineno)d ',
        "%Y-%m-%d %H:%M:%S"),  # This also supports log jump-to-source
    5: logging.Formatter(
        '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s',
        "%Y-%m-%d %H:%M:%S"),  # What I consider the best template; recommended
    6: logging.Formatter('%(name)s - %(asctime)-15s - %(filename)s - %(lineno)d - %(levelname)s: %(message)s',
                         "%Y-%m-%d %H:%M:%S"),
    7: logging.Formatter('%(asctime)s - %(name)s - "%(filename)s:%(lineno)d" - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S"),  # A template showing only the short filename and line number

    8: JsonFormatterJumpAble('%(asctime)s - %(name)s - %(levelname)s - %(message)s - "%(filename)s %(lineno)d -" ', "%Y-%m-%d %H:%M:%S", json_ensure_ascii=False),  # JSON log format for easy analysis

    9: logging.Formatter(
        '[p%(process)d_t%(thread)d] %(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s',
        "%Y-%m-%d %H:%M:%S"),  # Improved from 5; includes process and thread info.
    10: logging.Formatter(
        '[p%(process)d_t%(thread)d] %(asctime)s - %(name)s - "%(filename)s:%(lineno)d" - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S"),  # Improved from 7; includes process and thread info.
    11: logging.Formatter(
        f'({computer_ip},{computer_name})-[p%(process)d_t%(thread)d] %(asctime)s - %(name)s - "%(filename)s:%(lineno)d" - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S"),  # Improved from 7; includes process, thread, IP, and hostname.
}

FORMATTER_KIND = 5  # Default template index to use if get_logger_and_add_handlers does not specify one.
