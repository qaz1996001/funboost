import asyncio
import random
import time

from funboost import boost, FunctionResultStatusPersistanceConfig, BoosterParams, ConcurrentModeEnum
from funboost.core.current_task import get_current_taskid,fct
from funboost.core.task_id_logger import TaskIdLogger
import nb_log
from funboost.funboost_config_deafult import FunboostCommonConfig
from nb_log import LogManager

LOG_FILENAME_QUEUE_FCT = 'queue_fct.log'
# Using TaskIdLogger with a task_id log template; every log entry automatically includes task_id, making it easy to search logs and locate all logs for a specific task id.
task_id_logger = LogManager('namexx', logger_cls=TaskIdLogger).get_logger_and_add_handlers(
    log_filename='queue_fct.log',
    error_log_filename=nb_log.generate_error_file_name(LOG_FILENAME_QUEUE_FCT),
    formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER, )

# If not using TaskIdLogger to create the logger but still want the task_id log template, users must manually pass extra={'task_id': fct.task_id} when logging
common_logger = nb_log.get_logger('namexx2', formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER)


@boost(BoosterParams(queue_name='queue_test_fct', qps=2, concurrent_num=5, log_filename=LOG_FILENAME_QUEUE_FCT, function_timeout=20))
def f(a, b):
    print(get_current_taskid())

    # Each of the following log entries will automatically include task_id, making it easy to trace and diagnose issues.
    fct.logger.warning('If you do not want to create a logger object yourself, use fct.logger to log; fct.logger is the consumer logger for the current queue')
    task_id_logger.info(fct.function_result_status.task_id)  # Get the task id of the message
    task_id_logger.debug(fct.function_result_status.run_times)  # Get how many times the message has been retried
    task_id_logger.info(fct.full_msg)  # Get the full message, including values of a and b, publish time, task_id, etc.
    task_id_logger.debug(fct.function_result_status.publish_time_format)  # Get the publish time of the message
    task_id_logger.debug(fct.function_result_status.get_status_dict())  # Get task info as a dict.

    # If the user is not using a TaskIdLogger logger object but wants to display task_id in the template,
    common_logger.debug('Assuming logger is not TaskIdLogger type; to use task_id log template, pass extra={"task_id":fct.task_id}', extra={'task_id': fct.task_id})

    time.sleep(2)
    task_id_logger.debug(f'haha a: {a}')
    task_id_logger.debug(f'haha b: {b}')
    task_id_logger.info(a + b)
    if random.random() > 0.99:
        raise Exception(f'{a} {b} simulated error')

    return a + b


@boost(BoosterParams(queue_name='aio_queue_test_fct', qps=2, concurrent_num=5, log_filename=LOG_FILENAME_QUEUE_FCT, concurrent_mode=ConcurrentModeEnum.ASYNC, function_timeout=20))
async def aiof(a, b):
    # Each of the following log entries will automatically include task_id, making it easy to trace and diagnose issues.
    fct.logger.warning('If you do not want to create a logger object yourself, use fct.logger to log; fct.logger is the consumer logger for the current queue')
    task_id_logger.info(fct.function_result_status.task_id)  # Get the task id of the message
    task_id_logger.debug(fct.function_result_status.run_times)  # Get how many times the message has been retried
    task_id_logger.info(fct.full_msg)  # Get the full message, including values of a and b, publish time, task_id, etc.
    task_id_logger.debug(fct.function_result_status.publish_time_format)  # Get the publish time of the message
    task_id_logger.debug(fct.function_result_status.get_status_dict())  # Get task info as a dict.

    # If the user is not using a TaskIdLogger logger object but wants to display task_id in the template,
    common_logger.debug('Assuming logger is not TaskIdLogger type; to use task_id log template, pass extra={"task_id":fct.task_id}', extra={'task_id': fct.task_id})

    await asyncio.sleep(1)
    task_id_logger.debug(f'haha a: {a}')
    task_id_logger.debug(f'haha b: {b}')
    task_id_logger.info(a + b)
    if random.random() > 0.99:
        raise Exception(f'{a} {b} simulated error')

    return a + b


if __name__ == '__main__':
    # f(5, 6)  # 可以直接调用

    f.consume()
    aiof.consume()

    for i in range(0, 5):
        time.sleep(0.1)
        f.push(i, b=i * 2)
        aiof.push(i * 10, i * 20)


