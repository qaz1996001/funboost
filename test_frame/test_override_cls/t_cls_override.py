import random
import time

from funboost import boost, BrokerEnum, FunctionResultStatusPersistanceConfig, BoosterParams, ConcurrentModeEnum, AbstractConsumer, FunctionResultStatus


class MyConsumer(AbstractConsumer):
    def user_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus):
        print('Using the specified consumer_override_cls to customize or override methods')
        if current_function_result_status.success is True:
            print(f'Parameters {current_function_result_status.params} succeeded; result: {current_function_result_status.result}; simulating a WeChat notification')
        else:
            print(f'Parameters {current_function_result_status.params} failed; reason: {current_function_result_status.exception}; simulating sending an email')
        self.logger.debug(current_function_result_status.get_status_dict())  # Print the fields in current_function_result_status for the user.


@boost(BoosterParams(queue_name='test_redis_ack_use_timeout_queue', broker_kind=BrokerEnum.REDIS,
                     concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
                     log_level=10,  consumer_override_cls=MyConsumer,
                     is_show_message_get_from_broker=True))
def cost_long_time_fun(x):
    print(f'start {x}')
    time.sleep(2)
    if random.random()>0.5:
        raise ValueError('Simulated function execution error')
    print(f'end {x}')
    return x*2


if __name__ == '__main__':
    for i in range(100):
        cost_long_time_fun.push(i)
    cost_long_time_fun.consume()
