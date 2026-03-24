# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/18
"""
Micro-Batch Consumer Mixin

Functionality: Accumulates N messages before batch processing, instead of consuming one by one.
Applicable scenarios: Batch database writes, batch API calls, batch notifications, etc.

Usage: see test_frame/test_micro_batch/test_micro_batch_consumer.py

Usage method:
1. Using BoosterParams + MicroBatchConsumerMixin (recommended)
   @boost(BoosterParams(
       queue_name='batch_queue',
       consumer_override_cls=MicroBatchConsumerMixin,
       user_options={
           'micro_batch_size': 100,
           'micro_batch_timeout': 5.0,
       }
   ))
   def batch_task(items: list):
       db.bulk_insert(items)
"""

import asyncio
import threading
import time
import typing
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.concurrent_pool.async_helper import simple_run_in_executor
from funboost.constant import ConcurrentModeEnum,BrokerEnum
from funboost.core.func_params_model import BoosterParams
from funboost.core.helper_funs import get_func_only_params


class MicroBatchConsumerMixin(AbstractConsumer):
    """
    Micro-Batch Consumer Mixin

    Core principle:
    1. Overrides _submit_task method to accumulate messages in a buffer
    2. When batch_size messages are reached or timeout seconds have elapsed, batch-calls the consuming function
    3. The consuming function's input changes from a single object to list[dict]

    Configuration parameters (passed via user_options):
    - micro_batch_size: Batch size, default 100
    - micro_batch_timeout: Timeout in seconds, default 5.0

    Supported concurrency modes:
    - THREADING: Uses _run_batch (synchronous)
    - ASYNC: Uses _async_run_batch (asynchronous)
    """
    
    def custom_init(self):
        """Initialize micro-batch related configuration"""
        super().custom_init()
        
        # Read configuration from user_options (funboost recommends using user_options for custom configuration)
        user_options = self.consumer_params.user_options
        self._batch_size = user_options.get('micro_batch_size', 100)
        self._batch_timeout = user_options.get('micro_batch_timeout', 5.0)
        
        # Message buffer and lock
        self._batch_buffer: list = []
        self._batch_lock = threading.Lock()
        self._last_batch_time = time.time()
        
        # Determine if using async mode
        self._is_async_mode = self.consumer_params.concurrent_mode == ConcurrentModeEnum.ASYNC
        
        # Start timeout flush thread
        self._start_timeout_flush_thread()
        
        self.logger.info(
            f"MicroBatch consumer initialized, batch_size={self._batch_size}, timeout={self._batch_timeout}s, async_mode={self._is_async_mode}"
        )
    
    def _start_timeout_flush_thread(self):
        """Start timeout flush background thread"""
        def timeout_flush_loop():
            while True:
                time.sleep(min(1.0, self._batch_timeout / 2))
                with self._batch_lock:
                    if self._batch_buffer and self._is_timeout():
                        self._flush_batch()
        
        t = threading.Thread(
            target=timeout_flush_loop,
            daemon=True,
            name=f"micro_batch_flush_{self._queue_name}"
        )
        t.start()
    
    def _is_timeout(self) -> bool:
        """Check if timeout has been reached"""
        return time.time() - self._last_batch_time >= self._batch_timeout
    
    def _should_flush_batch(self) -> bool:
        """Check if the batch should be flushed"""
        return len(self._batch_buffer) >= self._batch_size
    
    def _submit_task(self, kw):
        """
        Override _submit_task method to accumulate messages in the buffer
        instead of immediately submitting to the concurrent pool for execution
        """
        # First perform message conversion and filtering (reuse parent class logic)
        kw['body'] = self._convert_msg_before_run(kw['body'])
        self._print_message_get_from_broker(kw['body'])
        
        # Pause consumption check
        # if self._judge_is_daylight():
        #     self._requeue(kw)
        #     time.sleep(self.time_interval_for_check_do_not_run_time)
        #     return
        
        self._judge_is_allow_run_by_cron()
        if self._last_judge_is_allow_run_by_cron_result is False:
            self._requeue(kw)
            time.sleep(self._time_interval_for_check_allow_run_by_cron)
            return
        
        # Extract function parameters
        
        function_only_params = get_func_only_params(kw['body'])
        kw['function_only_params'] = function_only_params
        
        # Accumulate to buffer
        with self._batch_lock:
            self._batch_buffer.append(kw)
            
            # Check if batch processing should be triggered
            if self._should_flush_batch():
                self._flush_batch()
        
        # Frequency control
        if self.consumer_params.is_using_distributed_frequency_control:
            active_num = self._distributed_consumer_statistics.active_consumer_num
            self._frequency_control(self.consumer_params.qps / active_num, self._msg_schedule_time_intercal * active_num)
        else:
            self._frequency_control(self.consumer_params.qps, self._msg_schedule_time_intercal)
    
    def _flush_batch(self):
        """
        Execute batch processing

        Note: The _batch_lock must already be held when calling this method
        """
        if not self._batch_buffer:
            return
        
        # Take out all buffered messages
        batch = self._batch_buffer[:]
        self._batch_buffer.clear()
        self._last_batch_time = time.time()
        
        batch_size = len(batch)
        self.logger.debug(f"Starting batch processing for {batch_size} messages")
        
        # Choose synchronous or asynchronous execution based on concurrency mode
        if self._is_async_mode:
            self.concurrent_pool.submit(self._async_run_batch, batch)
        else:
            self.concurrent_pool.submit(self._run_batch, batch)
    
    def _run_batch(self, batch: list):
        """
        Synchronously run consuming function in batch

        :param batch: List containing multiple kw dictionaries
        """
        t_start = time.time()
        batch_size = len(batch)
        
        # Extract function parameters from all messages
        items = [kw['function_only_params'] for kw in batch]

        try:
            # Call consuming function (input is a list)
            result = self.consuming_function(items)

            # Batch confirm consumption
            for kw in batch:
                self._confirm_consume(kw)
            
            t_cost = round(time.time() - t_start, 4)
            self.logger.info(f"Batch processing succeeded: {batch_size} messages, took {t_cost}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {batch_size} messages, error: {e}", exc_info=True)
            
            # 批量重回队列
            for kw in batch:
                try:
                    self._requeue(kw)
                except Exception as requeue_error:
                    self.logger.error(f"Failed to requeue message: {requeue_error}")
            
            # raise

    async def _async_run_batch(self, batch: list):
        """
        异步批量运行消费函数（支持 async def 消费函数）
        
        :param batch: 包含多个 kw 字典的列表
        """
        t_start = time.time()
        batch_size = len(batch)
        
        # 提取所有消息的函数参数
        items = [kw['function_only_params'] for kw in batch]
        
        try:
            # 调用消费函数（入参是 list）
            if asyncio.iscoroutinefunction(self.consuming_function):
                result = await self.consuming_function(items)
            else:
                # 同步函数在 executor 中运行
                result = await simple_run_in_executor(self.consuming_function, items)
            
            # 批量确认消费
            for kw in batch:
                await simple_run_in_executor(self._confirm_consume, kw)
            
            t_cost = round(time.time() - t_start, 4)
            self.logger.info(f"Batch processing succeeded (async): {batch_size} messages, took {t_cost}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Batch processing failed (async): {batch_size} messages, error: {e}", exc_info=True)
            
            # 批量重回队列
            for kw in batch:
                try:
                    await simple_run_in_executor(self._requeue, kw)
                except Exception as requeue_error:
                    self.logger.error(f"Failed to requeue message (async): {requeue_error}")
            
            # raise



class MicroBatchBoosterParams(BoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    consumer_override_cls: typing.Optional[typing.Type] = MicroBatchConsumerMixin  # 类型与父类保持一致
    user_options: dict = {
        'micro_batch_size': 10,        # 每批10条
        'micro_batch_timeout': 1.0,    # 1秒超时
    }
    qps: float = 100
    should_check_publish_func_params: bool = False  # 微批模式需要关闭入参校验
