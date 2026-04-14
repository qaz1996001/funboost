# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/23 0023 21:10
import time
from funboost.utils.redis_manager import RedisMixin
from funboost.utils import decorators
from funboost.core.serialization import Serialization
from funboost.constant import RedisKeys
"""
This module implements consumption confirmation based on Redis, which is relatively complex.
"""


# noinspection PyUnresolvedReferences

# noinspection PyUnresolvedReferences
class ConsumerConfirmMixinWithTheHelpOfRedisByHearbeat(RedisMixin):
    """
    Uses heartbeat to detect inactive consumers, and re-queues unack zset entries of inactive consumers back to the consumption queue.
    """
    

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        super().custom_init()
        self._unack_zset_name = f'{self._queue_name}__unack_id_{self.consumer_identification}'
        self._unack_registry_key = RedisKeys.gen_funboost_unack_registry_key_by_queue_name(self._queue_name)
        self.consumer_params.is_send_consumer_heartbeat_to_redis = True
        self._last_show_unacked_msg_num_log = 0
        self.consumer_params.is_send_consumer_heartbeat_to_redis = True
        # Plan C: Register unack key as a "full index" to avoid relying on heartbeat key for dead consumer records
        self.redis_db_frame.sadd(self._unack_registry_key, self._unack_zset_name)

    def start_consuming_message(self):
        super().start_consuming_message()
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()

    def _add_task_str_to_unack_zset(self, task_str, ):
        self.redis_db_frame.zadd(self._unack_zset_name, {task_str: time.time()})

    def _confirm_consume(self, kw):
        self.redis_db_frame.zrem(self._unack_zset_name, kw['task_str'])

    def _requeue_tasks_which_unconfirmed(self):
        lock_key = f'fsdf_lock__requeue_tasks_which_unconfirmed:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ).set_log_level(30) as lock:
            if lock.has_aquire_lock:
                # Plan C: Heartbeat key is only used to determine active consumers; full unack keys are obtained from registry
                heartbeat_redis_key = RedisKeys.gen_redis_hearbeat_set_key_by_queue_name(self._queue_name)
                all_heartbeat_records = self.redis_db_frame.smembers(heartbeat_redis_key)  # {"consumer_id&&timestamp", ...}
                alive_consumer_ids = set()
                for record in all_heartbeat_records:
                    parts = record.rsplit('&&', 1)
                    if parts:
                        alive_consumer_ids.add(parts[0])

                # Registry stores the specific unack key names
                all_unack_keys = self.redis_db_frame.smembers(self._unack_registry_key)
                unack_key_prefix = f'{self._queue_name}__unack_id_'


                # Display the number of pending tasks in the current unack queue
                if time.time() - self._last_show_unacked_msg_num_log > 600:
                    self.logger.info(f'{self._unack_zset_name} has '
                                     f'{self.redis_db_frame.zcard(self._unack_zset_name)} pending consumption confirmation tasks')
                    self._last_show_unacked_msg_num_log = time.time()

                # Handle dead consumer's unack queues (only process ack-able zset unack keys)
                for unack_key in all_unack_keys:
                    dead_consumer_id = unack_key[len(unack_key_prefix):]
                    if dead_consumer_id in alive_consumer_ids:
                        continue
                    current_queue_unacked_msg_queue_name = unack_key
                    self.logger.warning(f'{current_queue_unacked_msg_queue_name} belongs to a disconnected or closed consumer')
                    while True:
                        # [Optimization 1] Batch retrieve unacked tasks
                        unacked_task_list = self.redis_db_frame.zrevrange(current_queue_unacked_msg_queue_name, 0, 1000)
                        if not unacked_task_list:
                            break
                        
                        # Batch publish back to queue first
                        for unacked_task_str in unacked_task_list:
                            self.logger.warning(f'Re-queuing unacknowledged task from {current_queue_unacked_msg_queue_name} to {self._queue_name}'
                                                f' {unacked_task_str}')
                            self.publisher_of_same_queue.publish(unacked_task_str)
                        
                        # [Optimization 1] Batch delete tasks from unack queue to reduce IO operations
                        self.redis_db_frame.zrem(current_queue_unacked_msg_queue_name, *unacked_task_list)

                    # Clean up registry and unack key to prevent registry from growing indefinitely
                    
                    if self.redis_db_frame.zcard(current_queue_unacked_msg_queue_name) == 0:
                        self.redis_db_frame.delete(current_queue_unacked_msg_queue_name)
                        self.redis_db_frame.srem(self._unack_registry_key, current_queue_unacked_msg_queue_name)
                
