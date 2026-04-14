# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/9/19 0019 9:48
import datetime
import json
from pprint import pprint
import time
import copy
import traceback
from funboost import nb_print
from funboost.constant import RedisKeys

from funboost.core.func_params_model import TaskOptions, PublisherParams
from funboost.core.msg_result_getter import AsyncResult
from funboost.core.serialization import Serialization
from funboost.utils import time_util, decorators  # LoggerMixin is deprecated, Statistic class is no longer used
from funboost.utils.mongo_util import MongoMixin
from funboost.utils.redis_manager import RedisMixin
from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter, SingleQueueConusmerParamsGetter

# from test_frame.my_patch_frame_config import do_patch_frame_config
#
# do_patch_frame_config()


def get_mongo_table_name_by_queue_name(queue_name: str) -> str:
    """
    Get the corresponding MongoDB collection name for a given queue_name.

    Looks up function_result_status_persistance_conf.table_name from the queue configuration.
    If table_name is not configured, queue_name is used as the collection name.

    Args:
        queue_name: Queue name

    Returns:
        MongoDB collection name
    """
    queue_params = SingleQueueConusmerParamsGetter(queue_name).get_one_queue_params_use_cache()
    persistance_conf = queue_params['function_result_status_persistance_conf']
    table_name = persistance_conf.get('table_name') or queue_name
    return table_name 


def get_all_queue_table_info() -> dict:
    """
    Get the mapping of all queues and their corresponding MongoDB collection names.

    Returns:
        {queue_name: table_name, ...}
    """
    result = {}
    queues_config = QueuesConusmerParamsGetter().get_queues_params()
    for queue_name, params in queues_config.items():
        persistance_conf = params['function_result_status_persistance_conf']
        table_name = persistance_conf.get('table_name') or queue_name
        result[queue_name] = table_name 
    return result


def get_cols(queue_name_search: str):
    """
    Get the list of queues and return the record count for each queue's corresponding MongoDB collection.

    No longer uses db.list_collection_names(); instead retrieves collection names from queue configuration.
    Note: Because multiple queues may share the same collection, queries must include a queue_name condition.
    """
    db = MongoMixin().mongo_db_task_status

    # Get all queues and their corresponding collection names from queue configuration
    queue_table_map = get_all_queue_table_info()

    result = []
    for queue_name, table_name in queue_table_map.items():
        # Filter by search criteria
        if queue_name_search and queue_name_search not in queue_name:
            continue

        try:
            # Must include queue_name condition because multiple queues may share the same collection
            count = db.get_collection(table_name).count_documents({'queue_name': queue_name})
        except Exception:
            count = 0

        result.append({
            'collection_name': queue_name,  # Returns queue name (used for frontend display and subsequent queries)
            'table_name': table_name,       # Actual MongoDB collection name
            'count': count
        })
    
    return result


def query_result(queue_name, start_time, end_time, is_success, function_params: str, page, task_id: str = ''):
    """
    Query function execution results.

    Args:
        queue_name: Queue name (not the collection name; will be automatically converted to the corresponding MongoDB collection name)

    Note: Because multiple queues may share the same collection, queries must include a queue_name condition.
    """
    query_kw = copy.copy(locals())
    t0 = time.time()
    if not queue_name:
        return []
    db = MongoMixin().mongo_db_task_status

    # Get the actual MongoDB collection name from the queue name
    table_name = get_mongo_table_name_by_queue_name(queue_name)

    # Base condition: must include queue_name because multiple queues may share the same collection
    condition = {'queue_name': queue_name}

    # If task_id is provided, ignore other conditions (time range, run status, etc.) and query by task_id directly
    if task_id and task_id.strip():
        condition.update({'task_id': {'$regex': f'^{task_id.strip()}'}})
    else:
        # Normal query: use time range and other conditions
        condition.update({
            'insert_time': {'$gt': time_util.DatetimeConverter(start_time).datetime_obj,
                            '$lt': time_util.DatetimeConverter(end_time).datetime_obj},
        })
        if is_success in ('2', 2, True):
            condition.update({"success": True})
        elif is_success in ('3', 3, False):
            condition.update({"success": False})
        if function_params.strip():
            condition.update({'params_str': {'$regex': function_params.strip()}})

    # nb_print(col_name)
    # nb_print(condition)
    # with decorators.TimerContextManager():
    # Sort by time in descending order, newest first
    results = list(db.get_collection(table_name).find(condition, {'insert_time': 0, 'utime': 0}).sort([('time_start', -1)]).skip(int(page) * 100).limit(100))
    # nb_print(results)
    nb_print(time.time() -t0, query_kw, len(results), f'table: {table_name}')
    return results


def get_speed(queue_name, start_time, end_time):
    """
    Get consumption rate statistics for a specified time range.

    Args:
        queue_name: Queue name (not the collection name; will be automatically converted to the corresponding MongoDB collection name)

    Note: Because multiple queues may share the same collection, queries must include a queue_name condition.
    """
    db = MongoMixin().mongo_db_task_status

    # Get the actual MongoDB collection name from the queue name
    table_name = get_mongo_table_name_by_queue_name(queue_name)

    # Base condition: must include queue_name because multiple queues may share the same collection
    condition = {
        'queue_name': queue_name,
        'insert_time': {'$gt': time_util.DatetimeConverter(start_time).datetime_obj,
                        '$lt': time_util.DatetimeConverter(end_time).datetime_obj},
    }
    # condition = {
    #     'insert_time_str': {'$gt': time_util.DatetimeConverter(time.time() - 60).datetime_str},
    # }
    # nb_print(condition)
    with decorators.TimerContextManager():
        # success_num = db.get_collection(table_name).count({**{'success': True}, **condition})
        # fail_num = db.get_collection(table_name).count({**{'success': False}, **condition})
        success_num = db.get_collection(table_name).count_documents({**{'success': True,'run_status':'finish'}, **condition})
        fail_num = db.get_collection(table_name).count_documents({**{'success': False,'run_status':'finish'}, **condition})
        qps = (success_num + fail_num) / (time_util.DatetimeConverter(end_time).timestamp - time_util.DatetimeConverter(start_time).timestamp)
        return {'success_num': success_num, 'fail_num': fail_num, 'qps': round(qps, 1)}




def get_consume_speed_curve(queue_name: str, start_time: str, end_time: str, granularity: str = 'auto'):
    """
    Get consumption rate curve data.

    Args:
        queue_name: Queue name (not the collection name; will be automatically converted to the corresponding MongoDB collection name)
        start_time: Start time, format 'YYYY-MM-DD HH:MM:SS'
        end_time: End time, format 'YYYY-MM-DD HH:MM:SS'
        granularity: Time granularity: 'second', 'minute', 'hour', 'day', or 'auto'

    Returns:
        {
            'time_arr': [...],
            'success_arr': [...],
            'fail_arr': [...],
            'total_success': int,
            'total_fail': int,
            'granularity': str
        }
    """
    db = MongoMixin().mongo_db_task_status

    # Get the actual MongoDB collection name from the queue name
    table_name = get_mongo_table_name_by_queue_name(queue_name)

    start_dt = time_util.DatetimeConverter(start_time).datetime_obj
    end_dt = time_util.DatetimeConverter(end_time).datetime_obj

    # Calculate time span (seconds)
    time_span = (end_dt - start_dt).total_seconds()

    # Automatically select granularity
    if granularity == 'auto':
        if time_span <= 120:  # <= 2 minutes
            granularity = 'second'
        elif time_span <= 3600:  # <= 1 hour
            granularity = 'minute'
        elif time_span <= 86400 * 2:  # <= 2 days
            granularity = 'hour'
        else:
            granularity = 'day'

    # Set time format and step size based on granularity
    if granularity == 'second':
        time_format = '%Y-%m-%d %H:%M:%S'
        step = datetime.timedelta(seconds=1)
        max_points = 120
    elif granularity == 'minute':
        time_format = '%Y-%m-%d %H:%M'
        step = datetime.timedelta(minutes=1)
        max_points = 120
    elif granularity == 'hour':
        time_format = '%Y-%m-%d %H:00'
        step = datetime.timedelta(hours=1)
        max_points = 168  # 7 days
    else:  # day
        time_format = '%Y-%m-%d'
        step = datetime.timedelta(days=1)
        max_points = 60
    
    # Limit the number of data points to avoid too many
    actual_points = int(time_span / step.total_seconds()) + 1
    if actual_points > max_points:
        # Adjust step size
        step = datetime.timedelta(seconds=time_span / max_points)
        actual_points = max_points
    
    time_arr = []
    success_arr = []
    fail_arr = []
    total_success = 0
    total_fail = 0
    
    current = start_dt
    while current < end_dt:
        next_time = current + step
        if next_time > end_dt:
            next_time = end_dt
        
        # Base condition: must include queue_name because multiple queues may share the same collection
        condition_base = {
            'queue_name': queue_name,
            'insert_time': {'$gte': current, '$lt': next_time}
        }
        
        try:
            success_count = db.get_collection(table_name).count_documents({**condition_base, 'success': True, 'run_status': 'finish'})
            fail_count = db.get_collection(table_name).count_documents({**condition_base, 'success': False, 'run_status': 'finish'})
        except Exception as e:
            success_count = 0
            fail_count = 0
        
        time_arr.append(current.strftime(time_format))
        success_arr.append(success_count)
        fail_arr.append(fail_count)
        total_success += success_count
        total_fail += fail_count
        
        current = next_time
    
    return {
        'time_arr': time_arr,
        'success_arr': success_arr,
        'fail_arr': fail_arr,
        'total_success': total_success,
        'total_fail': total_fail,
        'granularity': granularity,
        'start_time': start_time,
        'end_time': end_time
    }


if __name__ == '__main__':
    pass
