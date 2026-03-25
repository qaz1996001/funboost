
from funboost import  BoosterParams, BrokerEnum, FunctionResultStatusPersistanceConfig



class Project1BoosterParams(BoosterParams):
    project_name:str = 'test_project1'  # Core config: project name. Once set, web interfaces can focus only on queues under this project, reducing noise from unrelated queues.
    broker_kind:str = BrokerEnum.REDIS_BRPOP_LPUSH
    is_send_consumer_heartbeat_to_redis : bool= True # Send heartbeat to Redis so that queue runtime info can be retrieved from Redis.
    is_using_rpc_mode:bool = True # This parameter must be set to True to support RPC functionality.
    booster_group : str = 'test_group1' # Convenient for starting consumers by group
    should_check_publish_func_params:bool = True # Whether to validate message content when publishing; incorrect message format immediately returns an error from the interface.
    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_result=True, is_save_status=True, expire_seconds=7 * 24 * 3600, is_use_bulk_insert=False,
        table_name='test_project1_function_result_status'
        )
