# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
"""
This is the enhanced version of Redis consumption with acknowledgment, so it is much more complex than redis_consumer implementation.
This ensures that tasks are never lost no matter how many times the script is stopped and restarted.
"""
import json
import time
from deprecated.sphinx import deprecated
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.consumers.confirm_mixin import ConsumerConfirmMixinWithTheHelpOfRedisByHearbeat


class RedisConsumerAckAble(ConsumerConfirmMixinWithTheHelpOfRedisByHearbeat, AbstractConsumer, ):
    """
    Restarting code at will does not lose tasks. Uses Redis heartbeat to re-queue all unconfirmed queues with expired heartbeats. This doesn't need to wait 10 minutes, and the detection is more precise.
    Implemented using Redis as middleware. Fetched messages are simultaneously placed in a set representing the unack consumption state. This supports arbitrary shutdown and power loss of machines and Python processes.
    The processing logic is very similar to celery's configuration with task_reject_on_worker_lost = True and task_acks_late = True.

    lua_4 = '''
   local v = redis.call("lpop", KEYS[1])
   if v then
   redis.call('rpush',KEYS[2],v)
    end
   return v'''
    # script_4 = r.register_script(lua_4)
    #
    # print(script_4(keys=["text_pipelien1","text_pipelien1b"]))
    """



    # def _dispatch_task000(self):
    #     # 可以采用lua脚本，也可以采用redis的watch配合pipeline使用。比代码分两行pop和zadd比还能减少一次io交互，还能防止丢失小概率一个任务。
    #     lua = '''
    #                  local v = redis.call("lpop", KEYS[1])
    #                  if v then
    #                  redis.call('zadd',KEYS[2],ARGV[1],v)
    #                   end
    #                  return v 
    #             '''
    #     script = self.redis_db_frame.register_script(lua)
    #     while True:
    #         return_v = script(keys=[self._queue_name, self._unack_zset_name], args=[time.time()])
    #         if return_v:
    #             task_str = return_v
    #             self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：     {task_str}  ')
    #             kw = {'body': task_str, 'task_str': task_str}
    #             self._submit_task(kw)
    #         else:
    #             # print('xiuxi')
    #             time.sleep(0.5)

    def custom_init(self):
        super().custom_init()
        self.pull_msg_batch_size = self.consumer_params.broker_exclusive_config['pull_msg_batch_size']
        self.pull_initial_interval = self.consumer_params.broker_exclusive_config.get('pull_base_interval',0.01) # This was added later to prevent config from redis metadata causing consumer creation errors, using get.
        self.pull_max_interval = self.consumer_params.broker_exclusive_config.get('pull_max_interval',2)

        

    def _dispatch_task(self):
        lua = f'''
                     local task_list = redis.call("lrange", KEYS[1],0,{self.pull_msg_batch_size-1})
                     redis.call("ltrim", KEYS[1],{self.pull_msg_batch_size},-1)
                     if (#task_list > 0) then
                        for task_index,task_value in ipairs(task_list)
                        do
                            redis.call('zadd',KEYS[2],ARGV[1],task_value)
                        end
                        return task_list
                    else
                        --local v = redis.call("blpop",KEYS[1],4)      
                        --return v
                      end

                '''
        """
        local v = redis.call("blpop",KEYS[1],60)  # redis 的lua 脚本禁止使用blpop
        local v = redis.call("lpop",KEYS[1])
        """
        
        script = self.redis_db_frame.register_script(lua)
        sleep_time = self.pull_initial_interval
        while True:
            task_str_list = script(keys=[self._queue_name, self._unack_zset_name], args=[time.time()])
            if task_str_list:
                sleep_time = self.pull_initial_interval # Has messages, reset to initial value
                self._print_message_get_from_broker( task_str_list)
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {task_str_list}  ')
                for task_str in task_str_list:
                    kw = {'body': task_str, 'task_str': task_str}
                    self._submit_task(kw)
            else:
                time.sleep(sleep_time)
                sleep_time = min(sleep_time * 2, self.pull_max_interval)  # Exponential backoff to increase polling interval, instead of using a fixed interval.

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))
