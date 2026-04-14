
"""
A contrib module for saving function result status to MySQL, PostgreSQL, etc.,
since the default storage backend is MongoDB.

You can specify user_custom_record_process_info_func=save_result_status_to_sqlalchemy in @boost.
"""


import copy
import functools
import json

from db_libs.sqla_lib import SqlaReflectHelper
from sqlalchemy import create_engine

from funboost import boost, FunctionResultStatus, funboost_config_deafult




def _gen_insert_sql_and_values_by_dict(dictx: dict):
    key_list = [f'`{k}`' for k in dictx.keys()]
    fields = ", ".join(key_list)

    # Build placeholder string
    placeholders = ", ".join(['%s'] * len(dictx))

    # Build insert statement
    insert_sql = f"INSERT INTO funboost_consume_results ({fields}) VALUES ({placeholders})"

    # Get the values from the data dictionary as the values to insert
    values = tuple(dictx.values())
    values_new = tuple([json.dumps(v) if isinstance(v, dict) else v for v in values])
    return insert_sql, values_new


def _gen_insert_sqlalchemy(dictx: dict):
    key_list = [f'`{k}`' for k in dictx.keys()]
    fields = ", ".join(key_list)

    value_list = dictx.keys()
    value_list_2 = [f':{f}' for f in value_list]
    values = ", ".join(value_list_2)

    # Build insert statement
    insert_sql = f"INSERT INTO funboost_consume_results ({fields}) VALUES ({values})"

    return insert_sql


@functools.lru_cache()
def get_sqla_helper():
    enginex = create_engine(
        funboost_config_deafult.BrokerConnConfig.SQLACHEMY_ENGINE_URL,
        max_overflow=10,  # Maximum additional connections beyond the pool size
        pool_size=50,  # Connection pool size
        pool_timeout=30,  # Maximum wait time when no connection is available in the pool, otherwise raises an error
        pool_recycle=3600,  # How often to recycle (reset) connections in the thread pool
        echo=True)
    sqla_helper = SqlaReflectHelper(enginex)
    t_funboost_consume_results = sqla_helper.base_classes.funboost_consume_results
    return enginex, sqla_helper, t_funboost_consume_results


def save_result_status_to_sqlalchemy(function_result_status: FunctionResultStatus):
    """ The function_result_status variable contains various rich information that users can access.
    This is a user-defined hook function for recording function consumption information.

    Example: @boost('test_user_custom', user_custom_record_process_info_func=save_result_status_to_sqlalchemy)
    """
    enginex, sqla_helper, t_funboost_consume_results = get_sqla_helper()

    with sqla_helper.session as ss:
        status_dict = function_result_status.get_status_dict()
        status_dict_new = copy.copy(status_dict)
        for k, v in status_dict.items():
            if isinstance(v, dict):
                status_dict_new[k] = json.dumps(v)
        # sql = _gen_insert_sqlalchemy(status_dict) # This is the SQLAlchemy raw SQL insert approach.
        # ss.execute(sql, status_dict_new)
        ss.merge(t_funboost_consume_results(**status_dict_new))  # This is the ORM insert approach.
