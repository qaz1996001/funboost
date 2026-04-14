# -*- coding: utf-8 -*-
"""
High-performance in-memory queue consumer

Supports two modes:
1. Standard mode (default): Full funboost feature support
2. Ultra-fast mode (ultra_fast_mode=True): Skips most framework overhead and calls functions directly
   - Ultra-fast mode does not support: retry, filtering, delayed tasks, RPC, result persistence, etc.
   - Suitable for scenarios requiring extremely high performance without needing these features
"""
import time
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.queues.fastest_mem_queue import FastestMemQueues, FastestMemQueue
from funboost.core.helper_funs import get_func_only_params


class FastestMemQueueConsumer(AbstractConsumer):
    """
    High-performance in-memory queue consumer.

    broker_exclusive_config options:
    - pull_msg_batch_size: Number of messages to pull in batch, default 1
    - ultra_fast_mode: Whether to enable ultra-fast mode, default False
      Ultra-fast mode skips most framework overhead, improving performance 3-10x, but loses retry/filtering/delay features
    """

    @property
    def _mem_queue(self) -> FastestMemQueue:
        return FastestMemQueues.get_queue(self._queue_name)

    def _dispatch_task(self):
        batch_size = self.consumer_params.broker_exclusive_config.get('pull_msg_batch_size', 1)
        ultra_fast = self.consumer_params.broker_exclusive_config.get('ultra_fast_mode', False)
        
        if ultra_fast:
            self._dispatch_task_ultra_fast(batch_size)
        elif batch_size <= 1:
            self._dispatch_task_single()
        else:
            self._dispatch_task_batch(batch_size)

    def _dispatch_task_single(self):
        """Single message pull mode"""
        while True:
            task = self._mem_queue.get()
            kw = {'body': task}
            self._submit_task(kw)

    def _dispatch_task_batch(self, batch_size: int):
        """Batch pull mode"""
        while True:
            tasks = self._mem_queue.get_batch_block(max_count=batch_size)
            for task in tasks:
                kw = {'body': task}
                self._submit_task(kw)

    def _dispatch_task_ultra_fast(self, batch_size: int):
        """
        Ultra-fast mode: Skips most framework overhead and calls functions directly

        Unsupported features: retry, filtering, delayed tasks, RPC, result persistence, metric statistics, etc.
        """
        func = self.consuming_function
        queue = self._mem_queue
        
        # Cache frequently used variables to avoid attribute access overhead
        count = 0
        last_log_time = time.time()
        
        if batch_size <= 1:
            # Single message ultra-fast mode
            while True:
                task = queue.get()
                # Directly extract function parameters and call
                if isinstance(task, dict):
                    params = get_func_only_params(task)
                    func(**params)
                else:
                    # If it's a string, conversion is needed
                    from funboost.core.serialization import Serialization
                    task_dict = Serialization.to_dict(task)
                    params = get_func_only_params(task_dict)
                    func(**params)
                
                count += 1
                # Output statistics every 10 seconds
                current_time = time.time()
                if current_time - last_log_time > 10:
                    self.logger.info(f'[Ultra-fast mode] Executed function [{func.__name__}] {count} times in 10 seconds')
                    count = 0
                    last_log_time = current_time
        else:
            # Batch ultra-fast mode
            while True:
                tasks = queue.get_batch_block(max_count=batch_size)
                for task in tasks:
                    if isinstance(task, dict):
                        params = get_func_only_params(task)
                        func(**params)
                    else:
                        from funboost.core.serialization import Serialization
                        task_dict = Serialization.to_dict(task)
                        params = get_func_only_params(task_dict)
                        func(**params)
                    count += 1
                
                current_time = time.time()
                if current_time - last_log_time > 10:
                    self.logger.info(f'[Ultra-fast mode] Executed function [{func.__name__}] {count} times in 10 seconds')
                    count = 0
                    last_log_time = current_time

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self._mem_queue.put(kw['body'])
