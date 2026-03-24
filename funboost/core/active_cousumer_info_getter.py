"""
The functionality of this module is ideal for developing a monitoring dashboard or admin backend for funboost.
    - ActiveCousumerProcessInfoGetter  Get active consumer process info for queues
    - QueuesConusmerParamsGetter  Get configuration parameters and runtime info for all queues
    - SingleQueueConusmerParamsGetter  Get configuration parameters and runtime info for a single queue


The web interfaces in the following 3 Python files mainly use the functionality of this module (funboost.faas).




The role of care_project_name:
    - None : Cares about all queue info stored in Redis
    - str : Only cares about queue info for the specified project_name

"""


import json
import threading
import time
import typing
import uuid
import os
import copy

from funboost.factories.consumer_factory import ConsumerCacheProxy
from funboost.factories.publisher_factotry import get_publisher
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils.redis_manager import RedisMixin

from funboost.core.loggers import FunboostFileLoggerMixin,nb_log_config_default
from funboost.core.serialization import Serialization
from funboost.constant import RedisKeys
from funboost.core.booster import  Booster,BoosterRegistry, booster_registry_default,gen_pid_queue_name_key
from funboost.core.func_params_model import PublisherParams, BoosterParams
from funboost.core.function_result_status_saver import FunctionResultStatusPersistanceConfig
from funboost.core.consuming_func_iniput_params_check import FakeFunGenerator
from funboost.core.exceptions import QueueNameNotExists
from funboost.timing_job.timing_push import ApsJobAdder
from funboost.constant import EnvConst

class CareProjectNameEnv:
    env_name = EnvConst.FUNBOOST_FAAS_CARE_PROJECT_NAME
    @classmethod
    def set(cls, care_project_name: str):
        os.environ[cls.env_name] = care_project_name

    @classmethod
    def get(cls) -> typing.Optional[bool]:
        care_project_name =  os.environ.get(cls.env_name, None)
        if care_project_name in ('','all','None','null','none',None):
            return None
        return care_project_name

booster_registry_for_faas = BoosterRegistry(
    booster_registry_name='booster_registry_for_faas')


class RedisReportInfoGetterMixin:
    # Class attribute: cache shared across all instances
    _cache_all_queue_names = None
    _cache_all_queue_names_ts = 0
    _cache_queue_names_by_project = {}  # {project_name: {'data': [...], 'ts': timestamp}}
    _cache_ttl = 30  # Cache for 30 seconds

    def _init(self,care_project_name:typing.Optional[str]=None,):
        """
        Parameters:
            care_project_name
            Only care about boosters related to the specified project_name, only fetch runtime info for those queues from Redis.

            Avoids fetching unrelated booster info from Redis, reducing noise and improving performance.
        """
        if care_project_name is not None:
            self.care_project_name = care_project_name
        else:
            self.care_project_name = CareProjectNameEnv.get()

    def get_all_queue_names(self) ->list:
        """Get all queue names with a 30-second cache (class-level cache shared across all instances)"""
        current_time = time.time()

        # Check if cache is still valid
        if self._cache_all_queue_names is not None and (current_time - self._cache_all_queue_names_ts) < self._cache_ttl:
            return self._cache_all_queue_names

        # Cache expired, re-fetch from Redis
        if self.care_project_name:
            result = self.project_name_queues
        else:
            result = list(self.redis_db_frame.smembers(RedisKeys.FUNBOOST_ALL_QUEUE_NAMES))

        # Update cache
        self.__class__._cache_all_queue_names = result
        self.__class__._cache_all_queue_names_ts = current_time

        return result

    def get_queue_names_by_project_name(self,project_name:str) ->list:
        """Get queue names by project name with a 30-second cache (class-level cache shared across all instances)"""
        current_time = time.time()

        # Check if cache is still valid
        if project_name in self._cache_queue_names_by_project:
            cache_entry = self._cache_queue_names_by_project[project_name]
            if (current_time - cache_entry['ts']) < self._cache_ttl:
                return cache_entry['data']

        # Cache expired, re-fetch from Redis
        result = list(self.redis_db_frame.smembers(RedisKeys.gen_funboost_project_name_key(project_name)))

        # Update cache
        self.__class__._cache_queue_names_by_project[project_name] = {
            'data': result,
            'ts': current_time
        }

        return result
    
    @property
    def all_queue_names(self):
        return self.get_all_queue_names()

    @property
    def project_name_queues(self):
        return self.get_queue_names_by_project_name(self.care_project_name)

    def hmget_many_by_all_queue_names(self,key):
        # if self.care_project_name is False:
        #     return self.redis_db_frame.hgetall(key)
        # ret_list = self.redis_db_frame.hmget(key,fileds)
        # return  dict(zip(fileds, ret_list))
        if len(self.all_queue_names) == 0:
            err_msg  = f"""
            care_project_name is set to {self.care_project_name},

            make sure  you have set @boost(BoosterParams(is_send_consumer_heartbeat_to_redis=True,project_name=$project_name))

            """
            self.logger.error(err_msg)
            return {}
        ret_list = self.redis_db_frame.hmget(key,self.all_queue_names)
        ret_list_exlude_none = [i for i in ret_list if i is not None]
        return  dict(zip(self.all_queue_names, ret_list_exlude_none))
    
    def get_all_project_names(self):
        return list(self.redis_db_frame.smembers(RedisKeys.FUNBOOST_ALL_PROJECT_NAMES))
    
    
    


def _cvt_int(str_value:typing.Optional[str])->typing.Optional[int]:
    if str_value is None:
        return None
    return int(str_value)


def _sum_filed_from_active_consumers(active_consumers:typing.List[dict],filed:str):
    s = 0
    for c in active_consumers:
        # print(c)
        if c[filed]:
            # print(c[filed])
            s+=c[filed]
    return s


def _max_filed_from_active_consumers(active_consumers:typing.List[dict],filed:str):
    """Get the maximum value of a given field across all consumers"""
    max_val = None
    for c in active_consumers:
        val = c.get(filed)
        if val is not None:
            if max_val is None or val > max_val:
                max_val = val
    return max_val

class ActiveCousumerProcessInfoGetter(RedisMixin,RedisReportInfoGetterMixin,FunboostFileLoggerMixin):
    """
    Get consumer process info in a distributed environment.
    The 4 methods here require the corresponding function's @boost decorator to have is_send_consumer_heartbeat_to_redis=True,
    so that active heartbeats are automatically sent to Redis. Otherwise, consumer process info for that function cannot be queried.
    To use the consumer process info statistics feature, users must install Redis regardless of which message broker they use,
    and configure the Redis connection info in funboost_config.py.
    """

    def __init__(self,care_project_name:typing.Optional[str]=None):
        RedisReportInfoGetterMixin._init(self,care_project_name)

        

    def _get_all_hearbeat_info_by_redis_key_name(self, redis_key):
        results = self.redis_db_frame.smembers(redis_key)
        # print(type(results))
        # print(results)
        # If all machines and all processes are shut down, there is no remaining thread to perform cleanup; we still need to check the 15-second threshold here.
        active_consumers_processor_info_list = []
        for result in results:
            result_dict = json.loads(result)
            if  result_dict['queue_name'] not in self.get_all_queue_names():
                continue
            if self.timestamp() - result_dict['hearbeat_timestamp'] < 15:
                active_consumers_processor_info_list.append(result_dict)
                if self.timestamp() - result_dict['current_time_for_execute_task_times_every_unit_time'] > 30:
                    result_dict['last_x_s_execute_count'] = 0
                    result_dict['last_x_s_execute_count_fail'] = 0
        return active_consumers_processor_info_list

    def get_all_hearbeat_info_by_queue_name(self, queue_name) -> typing.List[typing.Dict]:
        """
        Query which active consumer processes exist for a given queue name.
        Example return value:
        [{
                "code_filename": "/codes/funboost/test_frame/my/test_consume.py",
                "computer_ip": "172.16.0.9",
                "computer_name": "VM_0_9_centos",
                "consumer_id": 140477437684048,
                "consumer_uuid": "79473629-b417-4115-b516-4365b3cdf383",
                "consuming_function": "f2",
                "hearbeat_datetime_str": "2021-12-27 19:22:04",
                "hearbeat_timestamp": 1640604124.4643965,
                "process_id": 9665,
                "queue_name": "test_queue72c",
                "start_datetime_str": "2021-12-27 19:21:24",
                "start_timestamp": 1640604084.0780013
            }, ...............]
        """
        redis_key = RedisKeys.gen_funboost_hearbeat_queue__dict_key_by_queue_name(queue_name)
        return self._get_all_hearbeat_info_by_redis_key_name(redis_key)

    def get_all_hearbeat_info_by_ip(self, ip=None) -> typing.List[typing.Dict]:
        """
        Query which active consumer processes exist for a given machine IP.
        If ip is not provided, queries the local machine's IP to find which consumer processes are running under the funboost framework.
        If ip is provided, queries consumer process info for any specified machine.
        The return format is the same as the get_all_hearbeat_dict_by_queue_name method above.
        """
        ip = ip or nb_log_config_default.computer_ip
        redis_key = RedisKeys.gen_funboost_hearbeat_server__dict_key_by_ip(ip)
        return self._get_all_hearbeat_info_by_redis_key_name(redis_key)

    def get_all_ips(self):
        return self.redis_db_frame.smembers(RedisKeys.FUNBOOST_ALL_IPS)
    
    def _get_all_hearbeat_info_partition_by_redis_keys(self, keys):
        
        # keys = [f'{redis_key_prefix}{queue_name}' for queue_name in queue_names]
        infos_map = {}
        for key in keys:
            infos = self.redis_db_frame.smembers(key)
            dict_key = key.replace(RedisKeys.FUNBOOST_HEARTBEAT_QUEUE__DICT_PREFIX, '').replace(RedisKeys.FUNBOOST_HEARTBEAT_SERVER__DICT_PREFIX, '')
            infos_map[dict_key] = []
            for info_str in infos:
                info_dict = json.loads(info_str)
                if  info_dict['queue_name'] not in self.get_all_queue_names():
                    continue
                if self.timestamp() - info_dict['hearbeat_timestamp'] < 15:
                    infos_map[dict_key].append(info_dict)
                    if self.timestamp() - info_dict['current_time_for_execute_task_times_every_unit_time'] > 30:
                        info_dict['last_x_s_execute_count'] = 0
                        info_dict['last_x_s_execute_count_fail'] = 0
        return infos_map

    def get_all_hearbeat_info_partition_by_queue_name(self) -> typing.Dict[typing.AnyStr, typing.List[typing.Dict]]:
        """Get active consumer process info for all queues, partitioned by queue name. No queue name input needed; Redis keys are scanned automatically. Avoid storing too many other business cache entries in the Redis DB specified in funboost_config.py."""
        queue_names = self.get_all_queue_names()
        infos_map = self._get_all_hearbeat_info_partition_by_redis_keys([RedisKeys.gen_funboost_hearbeat_queue__dict_key_by_queue_name(queue_name) for queue_name in queue_names])
        # self.logger.info(f'Active consumer process info for all queues partitioned by queue name: {json.dumps(infos_map, indent=4)}')
        return infos_map

    def get_all_hearbeat_info_partition_by_ip(self) -> typing.Dict[typing.AnyStr, typing.List[typing.Dict]]:
        """Get active consumer process info for all machines, partitioned by IP. No IP input needed; Redis keys are scanned automatically. Avoid storing too many other business cache entries in the Redis DB specified in funboost_config.py."""
        ips = self.get_all_ips()
        infos_map = self._get_all_hearbeat_info_partition_by_redis_keys([RedisKeys.gen_funboost_hearbeat_server__dict_key_by_ip(ip) for ip in ips])
        self.logger.info(f'Active consumer process info for all machines partitioned by IP: {json.dumps(infos_map, indent=4)}')
        return infos_map





class QueuesConusmerParamsGetter(RedisMixin, RedisReportInfoGetterMixin,FunboostFileLoggerMixin):
    """
    Get runtime info for all queues.
    The method get_queues_params_and_active_consumers returns the most comprehensive information.
    """
    def __init__(self,care_project_name:typing.Optional[str]=None):
        RedisReportInfoGetterMixin._init(self,care_project_name)


    def get_queues_params(self,)->dict:
        queue__consumer_params_map = self.hmget_many_by_all_queue_names(RedisKeys.FUNBOOST_QUEUE__CONSUMER_PARAMS,)   
        return {k:Serialization.to_dict(v)  for k,v in queue__consumer_params_map.items()}

    def get_pause_flag(self):
        queue__pause_map = self.hmget_many_by_all_queue_names(RedisKeys.REDIS_KEY_PAUSE_FLAG,)
        return {k:_cvt_int(v)  for k,v in queue__pause_map.items()}

    def get_msg_num(self,ignore_report_ts=False):
        queue__msg_count_info_map = self.hmget_many_by_all_queue_names(RedisKeys.QUEUE__MSG_COUNT_MAP,)
        queue__msg_count_dict = {}
        # print(queue__msg_count_info_map)
        for queue_name,info_json in queue__msg_count_info_map.items():
            info_dict = json.loads(info_json)
            if ignore_report_ts or (info_dict['report_ts'] > time.time() - 15 and info_dict['last_get_msg_num_ts'] > time.time() - 1200):
                queue__msg_count_dict[queue_name] = info_dict['msg_num_in_broker']
        return queue__msg_count_dict

    def get_queues_history_run_count(self,):
        queue__run_count_map = self.hmget_many_by_all_queue_names(RedisKeys.FUNBOOST_QUEUE__RUN_COUNT_MAP,)
        return {k:_cvt_int(v) for k,v in queue__run_count_map.items()}
    
    def get_queues_history_run_fail_count(self,):
        queue__run_fail_count_map = self.hmget_many_by_all_queue_names(RedisKeys.FUNBOOST_QUEUE__RUN_FAIL_COUNT_MAP,)
        return {k:_cvt_int(v) for k,v in queue__run_fail_count_map.items()}
    
    def get_queues_params_and_active_consumers(self):
        """Get parameters and active consumers for all queues"""
        queue__active_consumers_map = ActiveCousumerProcessInfoGetter(
            care_project_name=self.care_project_name
            ).get_all_hearbeat_info_partition_by_queue_name()

        queue__history_run_count_map = self.get_queues_history_run_count()
        queue__history_run_fail_count_map = self.get_queues_history_run_fail_count()

        queue__consumer_params_map  = self.get_queues_params()
        queue__pause_map = self.get_pause_flag()
        queue__msg_count_dict = self.get_msg_num(ignore_report_ts=True)
        queue_params_and_active_consumers = {}

        for queue, consumer_params in  queue__consumer_params_map.items():
            
            active_consumers = queue__active_consumers_map.get(queue, [])
            # print(queue,active_consumers)
            all_consumers_last_x_s_execute_count = _sum_filed_from_active_consumers(active_consumers,'last_x_s_execute_count')
            all_consumers_last_x_s_execute_count_fail = _sum_filed_from_active_consumers(active_consumers, 'last_x_s_execute_count_fail')
            all_consumers_last_x_s_total_cost_time = _sum_filed_from_active_consumers(active_consumers, 'last_x_s_total_cost_time')
            all_consumers_last_x_s_avarage_function_spend_time = round( all_consumers_last_x_s_total_cost_time / all_consumers_last_x_s_execute_count,3) if all_consumers_last_x_s_execute_count else None
            all_consumers_last_execute_task_time = _max_filed_from_active_consumers(active_consumers, 'last_execute_task_time')
            
            all_consumers_total_consume_count_from_start = _sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start')
            all_consumers_total_cost_time_from_start =_sum_filed_from_active_consumers(active_consumers, 'total_cost_time_from_start')
            all_consumers_avarage_function_spend_time_from_start = round(all_consumers_total_cost_time_from_start / all_consumers_total_consume_count_from_start,3) if all_consumers_total_consume_count_from_start else None

            queue_params_and_active_consumers[queue] = {
                'queue_params':consumer_params,
                'active_consumers':active_consumers,
                'pause_flag':queue__pause_map.get(queue,-1),
                'msg_num_in_broker':queue__msg_count_dict.get(queue,None),
                
                'history_run_count':queue__history_run_count_map.get(queue,None),
                'history_run_fail_count':queue__history_run_fail_count_map.get(queue,None),

                'all_consumers_last_x_s_execute_count':all_consumers_last_x_s_execute_count,
                'all_consumers_last_x_s_execute_count_fail':all_consumers_last_x_s_execute_count_fail,
                'all_consumers_last_x_s_avarage_function_spend_time':all_consumers_last_x_s_avarage_function_spend_time,
                'all_consumers_avarage_function_spend_time_from_start':all_consumers_avarage_function_spend_time_from_start,
                'all_consumers_total_consume_count_from_start':_sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start'),
                'all_consumers_total_consume_count_from_start_fail':_sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start_fail'),
                'all_consumers_last_execute_task_time':all_consumers_last_execute_task_time,
            }
        return queue_params_and_active_consumers
    
    def cycle_get_queues_params_and_active_consumers_and_report(self,daemon=True):
        time_interval = 10
        report_uuid = str(uuid.uuid4()) 
        def _inner():
            while True:
                t_start = time.time()
                # This function ensures only one place reports data, avoiding duplicate collection and reporting
                report_ts = self.timestamp()
                redis_report_uuid_ts_str = self.redis_db_frame.get(RedisKeys.FUNBOOST_LAST_GET_QUEUES_PARAMS_AND_ACTIVE_CONSUMERS_AND_REPORT__UUID_TS, )
                if redis_report_uuid_ts_str:
                    redis_report_uuid_ts = Serialization.to_dict(redis_report_uuid_ts_str)
                    if redis_report_uuid_ts['report_uuid'] != report_uuid and redis_report_uuid_ts['report_ts'] > report_ts - time_interval - 10 :
                        time.sleep(5) # Prevent CPU busy-waiting
                        continue
                self.redis_db_frame.set(RedisKeys.FUNBOOST_LAST_GET_QUEUES_PARAMS_AND_ACTIVE_CONSUMERS_AND_REPORT__UUID_TS,
                                        Serialization.to_json_str({'report_uuid':report_uuid, 'report_ts':report_ts}))
                
                queue_params_and_active_consumers = self.get_queues_params_and_active_consumers()
                for queue,item in queue_params_and_active_consumers.items():
                    if len(item['active_consumers']) == 0:
                        continue
                    report_data = {k:v for k,v in item.items() if k not in ['queue_params','active_consumers']}
                    
                    report_data['report_ts'] = report_ts
                    self.redis_db_frame.zadd(RedisKeys.gen_funboost_queue_time_series_data_key_by_queue_name(queue),
                                            {Serialization.to_json_str(report_data):report_ts} )
                    # Remove expired time-series data, keep only the last 1 day of data
                    self.redis_db_frame.zremrangebyscore(
                        RedisKeys.gen_funboost_queue_time_series_data_key_by_queue_name(queue),
                        0, report_ts - 86400
                    )
                # self.logger.info(f'Time-series data collection and reporting took {time.time() - t_start} seconds')

                time.sleep(time_interval)
        threading.Thread(target=_inner, daemon=daemon).start()

    
        



class SingleQueueConusmerParamsGetter(RedisMixin, RedisReportInfoGetterMixin,FunboostFileLoggerMixin):
    """
    Get runtime info for a single queue.
    The method get_one_queue_params_and_active_consumers returns the most comprehensive information.
    """
    queue__booster_params_cache :dict= {}
    # _pid_broker_kind_queue_name__booster_map = {}
    # _pid_broker_kind_queue_name__publisher_map = {}
    _lock_for_generate_publisher_booster = threading.Lock()
    

    def __init__(self,queue_name:str,care_project_name:typing.Optional[str]=None,is_use_local_booster:bool=None):
        RedisReportInfoGetterMixin._init(self,care_project_name)
        self.queue_name = queue_name
        self._check_booster_exists()
        self.is_use_local_booster = is_use_local_booster if is_use_local_booster is not None else os.environ.get(EnvConst.FUNBOOST_FAAS_IS_USE_LOCAL_BOOSTER, 'false').lower() == 'true'
        self._last_update_consuming_func_input_params_checker = 0
     
    
    def _check_booster_exists(self):
        if self.queue_name not in self.all_queue_names:
            err_msg = f'''
            queue_name {self.queue_name} not in all_queue_names {self.all_queue_names},  

            you have set care_project_name={self.care_project_name},

            '''
            self.logger.error(err_msg)
            raise QueueNameNotExists(err_msg,error_data={'queue_name':self.queue_name,'care_project_name':self.care_project_name})

    def get_one_queue_params(self)->dict:
        """
        Returns something like this — the JSON string serialization of booster_params.

        ```json
        {
  "queue_name": "test_funboost_faas_queue2",
  "broker_kind": "REDIS",
  "project_name": "test_project1",
  "concurrent_mode": "threading",
  "concurrent_num": 50,
  "specify_concurrent_pool": null,
  "specify_async_loop": null,
  "is_auto_start_specify_async_loop_in_child_thread": true,
  "qps": null,
  "is_using_distributed_frequency_control": false,
  "is_send_consumer_heartbeat_to_redis": true,
  "max_retry_times": 3,

  "is_push_to_dlx_queue_when_retry_max_times": false,
  "consuming_function_decorator": null,
  "function_timeout": null,
  "is_support_remote_kill_task": false,
  "log_level": 10,
  "logger_prefix": "",
  "create_logger_file": true,
  "logger_name": "",
  "log_filename": null,
  "is_show_message_get_from_broker": false,
  "is_print_detail_exception": true,
  "publish_msg_log_use_full_msg": false,
  "msg_expire_seconds": null,
  "do_task_filtering": false,
  "task_filtering_expire_seconds": 0,
  "function_result_status_persistance_conf": {
    "is_save_status": false,
    "is_save_result": false,
    "expire_seconds": 604800,
    "is_use_bulk_insert": false
  },
  "user_custom_record_process_info_func": null,
  "is_using_rpc_mode": true,
  "rpc_result_expire_seconds": 1800,
  "rpc_timeout": 1800,
  "delay_task_apscheduler_jobstores_kind": "redis",
#   "is_do_not_run_by_specify_time_effect": false,
#   "do_not_run_by_specify_time": [
#     "10:00:00",
#     "22:00:00"
#   ],
  "schedule_tasks_on_main_thread": false,
  "is_auto_start_consuming_message": false,
  "booster_group": "test_group1",
  "consuming_function": "<function sub at 0x00000272649BBA60>",
  "consuming_function_raw": "<function sub at 0x00000272649BBA60>",
  "consuming_function_name": "sub",
  "broker_exclusive_config": {
    "redis_bulk_push": 1,
    "pull_msg_batch_size": 100
  },
  "should_check_publish_func_params": true,
  "manual_func_input_params": {
    "is_manual_func_input_params": false,
    "must_arg_name_list": [],
    "optional_arg_name_list": []
  },
  "consumer_override_cls": null,
  "publisher_override_cls": null,
  "consuming_function_kind": "COMMON_FUNCTION",
  "user_options": {
    
  },
  "auto_generate_info": {
    "where_to_instantiate": "D:\\codes\\funboost\\examples\\example_faas\\task_funs_dir\\sub.py:5",
    "final_func_input_params_info": {
      "func_name": "sub",
      "func_position": "<function sub at 0x00000272649BBA60>",
      "is_manual_func_input_params": false,
      "all_arg_name_list": [
        "a",
        "b"
      ],
      "must_arg_name_list": [
        "a",
        "b"
      ],
      "optional_arg_name_list": []
    }
  }
}


        ```
        """
        one_queue_params =  self.redis_db_frame.hget('funboost_queue__consumer_parmas',self.queue_name)
        return Serialization.to_dict(one_queue_params)

    def get_one_queue_params_use_cache(self)->dict:
        if self.queue_name not in self.queue__booster_params_cache or time.time() - self.queue__booster_params_cache[self.queue_name]['get_from_redis_ts'] > 60:
            booster_params = self.get_one_queue_params()
            get_from_redis_ts = time.time()
            self.queue__booster_params_cache[self.queue_name] = {'booster_params':booster_params,'get_from_redis_ts':get_from_redis_ts}
        return self.queue__booster_params_cache[self.queue_name]['booster_params']
    

   
    @staticmethod
    def _reset_non_json_serializable_fields(booster_params_from_redis: dict):
        """
        Automatically reset all non-JSON-serializable fields in BoosterParams to None.

        Note: booster_params_from_redis is a dict retrieved from Redis, where non-serializable object values are stored as strings.
        Based on the BoosterParams type definitions, fields with non-serializable types need to be reset to None.
        """
        # Get the list of non-serializable field names (with caching)
        from funboost.core.pydantic_compatible_base import get_cant_json_serializable_fields
        non_serializable_fields = get_cant_json_serializable_fields(BoosterParams)

        # Reset these fields to None
        for field_name in non_serializable_fields:
            if field_name in booster_params_from_redis:
                booster_params_from_redis[field_name] = None

    def _gen_booster_by_local_booster(self) -> Booster:
        # Use the local booster. This approach also works — each project can start its own funboost web manager.
        # Before starting the funboost web manager, import the module containing the relevant booster, then call `start_funboost_web_manager()`.
        
        booster = booster_registry_default.get_or_create_booster_by_queue_name(self.queue_name)
        return booster

    def _gen_booster_by_redis_meta_info(self) -> Booster:
        # Generate a fake booster using Redis metadata. Some booster config fields are set to None because they are not JSON-serializable.
        # Disadvantage: it is not a real booster. Advantage: supports cross-project booster management and hot-reload.
        booster_params_raw = self.get_one_queue_params_use_cache()
        booster_params = copy.deepcopy(booster_params_raw) # Deep copy the mutable dict before modifying it below
        current_broker_kind = booster_params['broker_kind']
        
        # Use the registry's instance attribute dict as a cache
        key = gen_pid_queue_name_key(self.queue_name)
        existing_booster = booster_registry_for_faas.pid_queue_name__booster_map.get(key)
        
        if existing_booster:
            """
            FaaS mode supports hot-reload publishing without restarting the web service.
            In edge cases where the broker switches from Redis to RabbitMQ mid-flight,
            the booster must be re-instantiated to support hot-reload.
            """
            if existing_booster.boost_params.broker_kind == current_broker_kind: 
                 self._update_publisher_params_checker(existing_booster.publisher, booster_params)
                 return existing_booster

        with self._lock_for_generate_publisher_booster:
             # Double-checked locking
             existing_booster = booster_registry_for_faas.pid_queue_name__booster_map.get(key)
             if existing_booster and existing_booster.boost_params.broker_kind == current_broker_kind:
                 return existing_booster

             # Automatically reset all non-JSON-serializable fields to None (avoids hard-coding)
             # e.g. user_custom_record_process_info_func, consumer_override_cls, consuming_function_decorator, etc.
             self._reset_non_json_serializable_fields(booster_params)
             
             
             # Generate a new booster

             # Manually set required fields
             redis_final_func_input_params_info = booster_params['auto_generate_info']['final_func_input_params_info']
             fake_fun = FakeFunGenerator.gen_fake_fun_by_params(redis_final_func_input_params_info)
             booster_params['consuming_function'] = fake_fun
             booster_params['consuming_function_raw'] = fake_fun
             
             booster_params['is_fake_booster'] = True 
             # Critical: specify the registry so the booster is automatically registered into booster_registry_for_faas on instantiation, overwriting the old key
             booster_params['booster_registry_name'] = 'booster_registry_for_faas'

             booster_params['function_result_status_persistance_conf'] = FunctionResultStatusPersistanceConfig(is_save_status=False,is_save_result=False)
             
             

             booster_params_model = BoosterParams(**booster_params)
             
             booster = Booster(booster_params_model)(booster_params_model.consuming_function)
             
             self._update_publisher_params_checker(booster.publisher, booster_params)
             return booster

    def gen_booster_for_faas(self) -> Booster:
        if self.is_use_local_booster:
            return self._gen_booster_by_local_booster()
        return self._gen_booster_by_redis_meta_info()
    
    def gen_publisher_for_faas(self)->AbstractPublisher:
        booster = self.gen_booster_for_faas()
        return booster.publisher
    
   
    def generate_aps_job_adder(self,job_store_kind='redis',is_auto_start=True,is_auto_paused=True) -> ApsJobAdder:
        booster = self.gen_booster_for_faas()
        job_adder = ApsJobAdder(booster, job_store_kind=job_store_kind, is_auto_start=is_auto_start,is_auto_paused=is_auto_paused)
        return job_adder


    def _update_publisher_params_checker(self,publisher:AbstractPublisher,booster_params:dict):
        """
        If the function's input parameter definitions are changed after it goes live, publish_params_checker still needs to be updated
        so that parameter validity is correctly validated when publishing messages.
        """
        if  self._last_update_consuming_func_input_params_checker < time.time() - 60:
            self._last_update_consuming_func_input_params_checker = time.time()
            final_func_input_params_info = booster_params['auto_generate_info'].get('final_func_input_params_info',None)
            if final_func_input_params_info:
                publisher.publish_params_checker.update_check_params(final_func_input_params_info)



    def get_one_queue_pause_flag(self) ->int:
        """
        Returns the pause state of the queue: -1 means the queue does not exist, 0 means not paused, 1 means paused.
        """
        pause_flag = self.redis_db_frame.hget(RedisKeys.REDIS_KEY_PAUSE_FLAG,self.queue_name)
        if pause_flag is None:
            return -1
        return int(pause_flag)

    def get_one_queue_history_run_count(self,) ->int:
        return _cvt_int(self.redis_db_frame.hget(RedisKeys.FUNBOOST_QUEUE__RUN_COUNT_MAP,self.queue_name))
    
    def get_one_queue_history_run_fail_count(self,) ->int:
        return _cvt_int(self.redis_db_frame.hget(RedisKeys.FUNBOOST_QUEUE__RUN_FAIL_COUNT_MAP,self.queue_name))

    def get_one_queue_msg_num(self,ignore_report_ts=False) ->int:
        """
        Get the message count from heartbeat info reported to Redis.
        If ignore_report_ts is True and the last report time was long ago, the message count may be inaccurate.
        The reporting thread runs automatically alongside consumption; if consumption has not started, heartbeat reporting will stop.
        """
        msg_count_info = self.redis_db_frame.hget(RedisKeys.QUEUE__MSG_COUNT_MAP,self.queue_name)
        info_dict = json.loads(msg_count_info)
        if ignore_report_ts or (info_dict['report_ts'] > time.time() - 15 and info_dict['last_get_msg_num_ts'] > time.time() - 1200):
            return info_dict['msg_num_in_broker']
        return -1

    def get_one_queue_msg_num_realtime(self,) ->int:
        """
        Get the message count in real time directly from the broker.
        """
        try:
            publisher = self.gen_publisher_for_faas()
            return publisher.get_message_count()
        except Exception as e:
            self.logger.exception(f'Failed to get queue message count in real time: {e}')
            return -1



    def get_one_queue_params_and_active_consumers(self)->dict:
        active_consumers = ActiveCousumerProcessInfoGetter(
            care_project_name=self.care_project_name
            ).get_all_hearbeat_info_by_queue_name(self.queue_name)

        history_run_count = self.get_one_queue_history_run_count()
        history_run_fail_count = self.get_one_queue_history_run_fail_count()

        consumer_params  = self.get_one_queue_params()
        pause_flag = self.get_one_queue_pause_flag()
        # msg_num = self.get_one_queue_msg_num(ignore_report_ts=True)
        msg_num = self.get_one_queue_msg_num_realtime()

        # print(queue,active_consumers)
        all_consumers_last_x_s_execute_count = _sum_filed_from_active_consumers(active_consumers,'last_x_s_execute_count')
        all_consumers_last_x_s_execute_count_fail = _sum_filed_from_active_consumers(active_consumers, 'last_x_s_execute_count_fail')
        all_consumers_last_x_s_total_cost_time = _sum_filed_from_active_consumers(active_consumers, 'last_x_s_total_cost_time')
        all_consumers_last_x_s_avarage_function_spend_time = round( all_consumers_last_x_s_total_cost_time / all_consumers_last_x_s_execute_count,3) if all_consumers_last_x_s_execute_count else None
        all_consumers_last_execute_task_time = _max_filed_from_active_consumers(active_consumers, 'last_execute_task_time')
        
        all_consumers_total_consume_count_from_start = _sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start')
        all_consumers_total_cost_time_from_start =_sum_filed_from_active_consumers(active_consumers, 'total_cost_time_from_start')
        all_consumers_avarage_function_spend_time_from_start = round(all_consumers_total_cost_time_from_start / all_consumers_total_consume_count_from_start,3) if all_consumers_total_consume_count_from_start else None

        params_and_active_consumers = {
            'queue_params':consumer_params,
            'active_consumers':active_consumers,
            'pause_flag':pause_flag,
            'msg_num_in_broker':msg_num,
            
            'history_run_count':history_run_count,
            'history_run_fail_count':history_run_fail_count,

            'all_consumers_last_x_s_execute_count':all_consumers_last_x_s_execute_count,
            'all_consumers_last_x_s_execute_count_fail':all_consumers_last_x_s_execute_count_fail,
            'all_consumers_last_x_s_avarage_function_spend_time':all_consumers_last_x_s_avarage_function_spend_time,
            'all_consumers_avarage_function_spend_time_from_start':all_consumers_avarage_function_spend_time_from_start,
            'all_consumers_total_consume_count_from_start':_sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start'),
            'all_consumers_total_consume_count_from_start_fail':_sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start_fail'),
            'all_consumers_last_execute_task_time':all_consumers_last_execute_task_time,
        }
        return params_and_active_consumers

    
    def get_one_queue_time_series_data(self,start_ts=None,end_ts=None,curve_samples_count=None):
        res = self.redis_db_frame.zrangebyscore(
            RedisKeys.gen_funboost_queue_time_series_data_key_by_queue_name(self.queue_name),
            max(float(start_ts or 0),self.timestamp() - 86400) ,float(end_ts or -1),withscores=True)
        # print(res)
        series_data_all= [{'report_data':Serialization.to_dict(item[0]),'report_ts':item[1]} for item in res]
        if curve_samples_count is None:
            return series_data_all
        
        # Number of curve samples
        total_count = len(series_data_all)
        if total_count <= curve_samples_count:
            # If the original data count is less than or equal to the required sample count, return all data
            return series_data_all

        # Calculate the sampling step size
        step = total_count / curve_samples_count
        sampled_data = []

        # Sample data according to the step size
        for i in range(curve_samples_count):
            index = int(i * step)
            if index < total_count:
                sampled_data.append(series_data_all[index])
        
        return sampled_data

    def deprecate_queue(self):
        """
        Deprecate a queue - remove the queue name from Redis.
        1. Remove from the funboost_all_queue_names set
        2. Remove from the funboost.project_name:{project_name} set
        """
        # Remove from the all-queue-names set
        self.redis_db_frame.srem(RedisKeys.FUNBOOST_ALL_QUEUE_NAMES, self.queue_name)
        # Remove from the project queue-names set
        self.redis_db_frame.srem(RedisKeys.gen_funboost_project_name_key(self.care_project_name), self.queue_name)

    



if __name__ == '__main__':
    CareProjectNameEnv.set('test_project1')
    print(Serialization.to_json_str(QueuesConusmerParamsGetter().get_queues_params_and_active_consumers()))
    print(Serialization.to_json_str(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()))
    # QueuesConusmerParamsGetter().cycle_get_queues_params_and_active_consumers_and_report()
    print(SingleQueueConusmerParamsGetter('queue_test_g03t').get_one_queue_time_series_data(1749617883,1749621483))
   


    print(SingleQueueConusmerParamsGetter('test_funboost_faas_queue').get_one_queue_params_and_active_consumers())
    