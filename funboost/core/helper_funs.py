import time
import typing
from funboost.core.serialization import Serialization
from funboost.utils import uuid7 
from funboost.core.funboost_time import FunboostTime, fast_get_now_time_str


def get_publish_time(paramsx: dict):
    """
    :param paramsx:
    :return:
    """
    return paramsx.get('extra', {}).get('publish_time', None)


def get_publish_time_format(paramsx: dict):
    """
    :param paramsx:
    :return:
    """
    return paramsx.get('extra', {}).get('publish_time_format', None)

def get_task_id(msg:typing.Union[dict,str]):
    msg_dict = Serialization.to_dict(msg)
    return msg_dict.get('extra', {}).get('task_id', None)


def delete_keys_and_return_new_dict(dictx: dict, exclude_keys: list ):
    """
    Returns a new dictionary without the specified keys, i.e. the actual function input parameter dictionary.
    Optimization: uses dict comprehension instead of deepcopy + pop, improving performance 10-50x.
    """
    return {k: v for k, v in dictx.items() if k not in exclude_keys}

_DEFAULT_EXCLUDE_KEYS = frozenset(['extra'])

def get_func_only_params(dictx: dict)->dict:
    """
    Removes the extra field from the message and returns the actual function input parameter dictionary.
    :param dictx:
    :return:
    """
    return {k: v for k, v in dictx.items() if k not in _DEFAULT_EXCLUDE_KEYS}



def block_python_main_thread_exit():
    """

    https://funboost.readthedocs.io/zh-cn/latest/articles/c10.html#runtimeerror-cannot-schedule-new-futures-after-interpreter-shutdown

    Mainly used for scheduled task errors in Python 3.9+: RuntimeError: cannot schedule new futures after interpreter shutdown.
    If the main thread exits, apscheduler will throw this error. The while 1: time.sleep(100) loop is intended to prevent the main thread from exiting.
    """
    while 1:
        time.sleep(100)


run_forever = block_python_main_thread_exit


class MsgGenerater:
    @staticmethod
    def generate_task_id(queue_name:str) -> str:
        """
        UUIDv7 is a time-ordered UUID, part of the new generation UUID specification (RFC 9562, now standardized),
        designed specifically for databases/distributed systems. In a nutshell:
        UUIDv7 = "globally unique like UUID + monotonically increasing like Snowflake ID"
        """
        # return f'{queue_name}_result:{uuid.uuid4()}'
        return uuid7.uuid7_str()

    @staticmethod
    def generate_publish_time() -> float:
        return round(time.time(),4)


    @staticmethod
    def generate_publish_time_format() -> str:
        # return FunboostTime().get_str()  # Poor performance
        # return get_now_time_str_by_tz()  # 1 million calls in 2 seconds
        return fast_get_now_time_str() # 1 million calls in 0.4 seconds


    @classmethod
    def generate_pulish_time_and_task_id(cls,queue_name:str,task_id=None):
        extra_params = {'task_id': task_id or cls.generate_task_id(queue_name), 
                        'publish_time': cls.generate_publish_time(),  # Timestamp in seconds
                        'publish_time_format': cls.generate_publish_time_format() # Time string, e.g. 2025-12-25 10:00:00
                        
                        }
        return extra_params



if __name__ == '__main__':

    from funboost import FunboostCommonConfig

    print(FunboostTime())
    for i in range(1000000):
        # time.time()
        MsgGenerater.generate_publish_time_format()
        # FunboostTime().get_str()

        # datetime.datetime.now(tz=pytz.timezone(FunboostCommonConfig.TIMEZONE)).strftime(FunboostTime.FORMATTER_DATETIME_NO_ZONE)

    print(FunboostTime())