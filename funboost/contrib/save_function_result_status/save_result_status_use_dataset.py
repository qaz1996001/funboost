
"""
A contrib module for saving function result status to MySQL, PostgreSQL, etc.,
since the default storage backend is MongoDB.

You can specify user_custom_record_process_info_func=save_result_status_to_sqlalchemy in @boost.
"""

import os
import copy
import functools
import json
import threading

import dataset

from funboost import boost, FunctionResultStatus, funboost_config_deafult,AbstractConsumer



pid__db_map = {}
_lock = threading.Lock()
def get_db(connect_url) -> dataset.Database:
    """Wrapper function that checks the current PID to get the correct database connection"""
    pid = os.getpid()
    key = (pid, connect_url,)
    if key not in pid__db_map:
        with _lock:
            if key not in pid__db_map:
                pid__db_map[key] =  dataset.connect(connect_url)
    return pid__db_map[key]


connect_url = 'mysql+pymysql://root:123456@127.0.0.1:3306/testdb7'  # dataset or SQLAlchemy URL connection format

# Method 1: Use a function hook in the @boost decorator via user_custom_record_process_info_func
def save_result_status_use_dataset(result_status: FunctionResultStatus):
    db = get_db(connect_url)
    table = db['funboost_consume_results']
    table.upsert(result_status.get_status_dict(), ['_id'])

# Method 2: Use consumer_override_cls in the decorator and override user_custom_record_process_info_func
class ResultStatusUseDatasetMixin(AbstractConsumer):
    def user_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus):
        # print(current_function_result_status.get_status_dict())
        db = get_db(connect_url)
        table = db['funboost_consume_results']
        table.upsert(current_function_result_status.get_status_dict(), ['_id'])