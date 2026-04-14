# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import logging
import threading


from flask import Flask, request

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.function_result_status_saver import FunctionResultStatus
from funboost.core.msg_result_getter import FutureStatusResult
from funboost.core.serialization import Serialization




class HTTPConsumer(AbstractConsumer, ):
    """
    Consumer implemented using Flask as message queue
    """


    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # try:
        #     self._ip, self._port = self.queue_name.split(':')
        #     self._port = int(self._port)
        # except BaseException as e:
        #     self.logger.critical(f'When using http as a message queue, the queue name must be set like: 192.168.1.101:8200  format:  ip:port')
        #     raise e
        self._ip = self.consumer_params.broker_exclusive_config['host']
        self._port = self.consumer_params.broker_exclusive_config['port']
        if self._port is None:
            raise ValueError('please specify port')

    def _dispatch_task(self):
        """
        HTTP server implementation using Flask.
        Compared to aiohttp, Flask is a synchronous framework, avoiding async blocking issues.
        """
     

        # Create Flask application
        flask_app = Flask(__name__)
        # Disable Flask logging to avoid interfering with funboost logging
        flask_app.logger.disabled = True
        logging.getLogger('werkzeug').disabled = True
        
        @flask_app.route('/', methods=['GET'])
        def hello():
            """Health check endpoint"""
            return "Hello, from funboost (Flask version)"
        
        @flask_app.route('/queue', methods=['POST'])
        def recv_msg():
            """
            Core endpoint for receiving messages.
            Supports two call types:
            1. publish: Asynchronous publishing, returns immediately
            2. sync_call: Synchronous call, waits for result to return
            """
            try:
                # Get request data
                msg = request.form.get('msg')
                call_type = request.form.get('call_type', 'publish')
                
                if not msg:
                    return {"error": "msg parameter is required"}, 400
                
                # Construct message data
                kw = {
                    'body': msg,
                    'call_type': call_type,
                }
                
                if call_type == 'sync_call':
                    # Synchronous call: needs to wait for execution result
                    future_status_result = FutureStatusResult(call_type=call_type)
                    kw['future_status_result'] = future_status_result
                    
                    # Submit task to thread pool for execution
                    self._submit_task(kw)
                    
                    # Wait for task completion (with timeout)
                    if future_status_result.wait_finish(self.consumer_params.rpc_timeout):
                        # Return execution result
                        result = future_status_result.get_staus_result_obj()
                        return Serialization.to_json_str(
                            result.get_status_dict(without_datetime_obj=True)
                        )
                    else:
                        # Timeout handling
                        self.logger.error(f'sync_call wait timeout after {self.consumer_params.rpc_timeout}s')
                        return {"error": "execution timeout"}, 408
                        
                else:
                    # Async publish: submit task directly, return immediately
                    self._submit_task(kw)
                    return "finish"
                    
            except Exception as e:
                self.logger.error(f'Error processing HTTP request: {e}', exc_info=True)
                return {"error": str(e)}, 500
        
        # Start Flask server
        # Note: Flask is single-threaded by default, but funboost uses a thread pool for tasks, so threaded=True
        self.logger.info(f'Starting Flask HTTP server, listening on {self._ip}:{self._port}')

        # flask_app.run(
        #     host='0.0.0.0',  # listen on all interfaces
        #     port=self._port,
        #     debug=False,     # disable debug in production
        #     threaded=True,   # enable multi-threading support
        #     use_reloader=False,  # disable auto-reload
        # )

        import waitress
        waitress.serve(flask_app, host='0.0.0.0', port=self._port,threads=self.consumer_params.concurrent_num)

    def _frame_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, kw: dict):
        """
        Callback function after task execution completes.
        For sync_call mode, needs to notify the waiting HTTP request.
        """
        if kw['call_type'] == "sync_call":
            future_status_result: FutureStatusResult = kw['future_status_result']
            future_status_result.set_staus_result_obj(current_function_result_status)
            future_status_result.set_finish()
            # self.logger.info('sync_call task execution complete, notifying HTTP request to return result')

    def _confirm_consume(self, kw):
        """HTTP mode does not have consumption confirmation"""
        pass

    def _requeue(self, kw):
        """HTTP mode does not have requeue functionality"""
        pass
