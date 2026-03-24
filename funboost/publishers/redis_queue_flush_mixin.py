from funboost.constant import RedisKeys


class FlushRedisQueueMixin:
    # noinspection PyUnresolvedReferences
    def clear(self):
        self.redis_db_frame.delete(self._queue_name)
        self.logger.warning(f'Successfully cleared messages in queue {self._queue_name}')

        # Approach C: Prioritize getting all unack keys from the unack registry and delete directly (not dependent on whether heartbeat still contains dead consumers)
        registry_key = RedisKeys.gen_funboost_unack_registry_key_by_queue_name(self._queue_name)
        unack_keys_from_registry = self.redis_db_frame.smembers(registry_key)
        if unack_keys_from_registry:
            self.redis_db_frame.delete(*list(unack_keys_from_registry))
            self.redis_db_frame.delete(registry_key)
            self.logger.warning(f'Successfully cleared messages in queues {list(unack_keys_from_registry)}')

        # Compatibility fallback: old logic retained (for historical scenarios where registry is not yet enabled)
        # [Optimization] Get all consumer IDs from heartbeat set, directly construct unack queue names, avoid using scan command
        heartbeat_redis_key = RedisKeys.gen_redis_hearbeat_set_key_by_queue_name(self._queue_name)
        all_heartbeat_records = self.redis_db_frame.smembers(heartbeat_redis_key)
        
        unack_queue_name_list = []
        for record in all_heartbeat_records:
            parts = record.rsplit('&&', 1)
            if len(parts) >= 1:
                consumer_id = parts[0]
                unack_queue_name_list.append(f'{self._queue_name}__unack_id_{consumer_id}')
                unack_queue_name_list.append(f'unack_{self._queue_name}_{consumer_id}') # for brpoplpush
        
              
        if unack_queue_name_list:
            self.redis_db_frame.delete(*unack_queue_name_list)
            self.logger.warning(f'Successfully cleared messages in queues {unack_queue_name_list}')
