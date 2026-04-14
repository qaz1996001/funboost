"""
Flask out-of-the-box: simply use app.register_blueprint(flask_blueprint) to automatically add common routes
to the user's Flask application, including publishing messages, getting results by task_id, and getting queue message counts.



Usage:
    In the user's own Flask project:
       app.register_blueprint(flask_blueprint)



"""

import traceback
from flask import Blueprint, request, jsonify

from funboost import AsyncResult, TaskOptions
from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter, QueuesConusmerParamsGetter, CareProjectNameEnv, ActiveCousumerProcessInfoGetter
from funboost.faas.faas_util import gen_aps_job_adder
from funboost.core.loggers import get_funboost_file_logger



logger = get_funboost_file_logger(__name__)

# Create Blueprint instance for users to register into their own app
# Users can use app.register_blueprint(flask_blueprint)
flask_blueprint = Blueprint('funboost', __name__, url_prefix='/funboost')


@flask_blueprint.route("/publish", methods=['POST'])
def publish_msg():
    """
    Publish message endpoint.

    Request body example:
    {
        "queue_name": "test_queue",
        "msg_body": {"x": 1, "y": 2},
        "need_result": true,
        "timeout": 60
    }
    """
    status_and_result = None
    task_id = None

    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({
                "succ": False,
                "msg": "Request body must be in JSON format",
                "data": {
                    "task_id": None,
                    "status_and_result": None
                }
            }), 400

        queue_name = data.get('queue_name')
        msg_body = data.get('msg_body')
        need_result = data.get('need_result', False)
        timeout = data.get('timeout', 60)
        task_id_param = data.get('task_id')  # Optional: specify task_id

        # Validate required fields
        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name field is required",
                "data": {
                    "task_id": None,
                    "status_and_result": None
                }
            }), 400

        if not msg_body or not isinstance(msg_body, dict):
            return jsonify({
                "succ": False,
                "msg": "msg_body field is required and must be a dict",
                "data": {
                    "task_id": None,
                    "status_and_result": None
                }
            }), 400

        # BoostersManager.get_or_create_booster_by_queue_name obtains or creates a booster by queue_name in reverse.
        # No need for the user to manually determine the queue_name and then precisely use a specific consumer function.
        publisher = SingleQueueConusmerParamsGetter(queue_name).gen_publisher_for_faas()
        booster_params_by_redis = SingleQueueConusmerParamsGetter(queue_name).get_one_queue_params_use_cache()

        # Check if RPC mode is needed
        if need_result:
            # Publish with RPC mode enabled (synchronous)
            async_result = publisher.publish(
                msg_body,
                task_id=task_id_param,  # Optional: specify task_id (for retrying failed tasks)
                task_options=TaskOptions(is_using_rpc_mode=True)
            )
            task_id = async_result.task_id

            # Wait for result (synchronous)
            print(async_result.task_id, timeout)
            status_and_result = AsyncResult(async_result.task_id, timeout=timeout).status_and_result
        else:
            # Normal publish (synchronous), can specify task_id
            async_result = publisher.publish(msg_body, task_id=task_id_param)
            task_id = async_result.task_id

        return jsonify({
            "succ": True,
            "msg": f'{queue_name} queue, message published successfully',
            "data": {
                "task_id": task_id,
                "status_and_result": status_and_result
            }
        })

    except Exception as e:
        return jsonify({
            "succ": False,
            "msg": f'Failed to publish message {type(e)} {e} {traceback.format_exc()}',
            "data": {
                "task_id": task_id,
                "status_and_result": status_and_result
            }
        }), 500


@flask_blueprint.route("/get_result", methods=['GET'])
def get_result():
    """
    Get task execution result by task_id.

    Query parameters:
        task_id: str - Task ID (required)
        timeout: int - Timeout in seconds, default 5
    """
    try:
        task_id = request.args.get('task_id')
        timeout = int(request.args.get('timeout', 5))

        if not task_id:
            return jsonify({
                "succ": False,
                "msg": "task_id parameter is required",
                "data": {
                    "task_id": None,
                    "status_and_result": None
                }
            }), 400

        # Try to get the result with a short default timeout to prevent indefinite blocking
        # Note: if the task is still running, AsyncResult will block until timeout
        # If the task has already completed and expired, this may return None
        status_and_result = AsyncResult(task_id, timeout=timeout).status_and_result

        if status_and_result is not None:
            return jsonify({
                "succ": True,
                "msg": "Retrieved successfully",
                "data": {
                    "task_id": task_id,
                    "status_and_result": status_and_result
                }
            })
        else:
            return jsonify({
                "succ": False,
                "msg": "No result retrieved (possibly expired, not yet started, or timed out)",
                "data": {
                    "task_id": task_id,
                    "status_and_result": None
                }
            })

    except Exception as e:
        return jsonify({
            "succ": False,
            "msg": f"Error getting result: {str(e)}",
            "data": {
                "task_id": task_id if 'task_id' in locals() else None,
                "status_and_result": None
            }
        }), 500


@flask_blueprint.route("/get_msg_count", methods=['GET'])
def get_msg_count():
    """
    Get message count by queue_name.

    Query parameters:
        queue_name: str - Queue name (required)
    """
    try:
        queue_name = request.args.get('queue_name')

        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name parameter is required",
                "data": {
                    "queue_name": None,
                    "count": -1
                }
            },), 400

        publisher = SingleQueueConusmerParamsGetter(queue_name).gen_publisher_for_faas()
        # Get message count (Note: some middleware may not support accurate counting, returns -1)
        count = publisher.get_message_count()

        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "data": {
                "queue_name": queue_name,
                "count": count
            }
        })

    except Exception as e:
        return jsonify({
            "succ": False,
            "msg": f"Failed to get message count: {str(e)}",
            "data": {
                "queue_name": queue_name if 'queue_name' in locals() else None,
                "count": -1
            }
        }), 500


@flask_blueprint.route("/get_all_queues", methods=['GET'])
def get_all_queues():
    """
    Get all registered queue names.

    Returns a list of all queue names registered via the @boost decorator.
    """
    try:
        # Get all queue names
        all_queues = QueuesConusmerParamsGetter().get_all_queue_names()

        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "data": {
                "queues": all_queues,
                "count": len(all_queues)
            }
        })

    except Exception as e:
        return jsonify({
            "succ": False,
            "msg": f"Failed to get all queues: {str(e)}",
            "data": {
                "queues": [],
                "count": 0
            }
        }), 500




@flask_blueprint.route("/clear_queue", methods=['POST'])
def clear_queue():
    """
    Clear all messages in the queue.

    Request body (JSON):
        {
            "queue_name": "queue name"
        }

    Returns:
        Result of the clear operation.

    Notes:
        This endpoint clears all pending messages in the specified queue.
        Warning: this operation is irreversible, use with caution!

    Note:
        broker_kind is automatically obtained from the registered booster, no need to specify manually.
    """
    try:
        data = request.get_json()
        queue_name = data.get('queue_name')

        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name field is required",
                "data": None
            }), 400

        # Automatically get the corresponding publisher by queue_name
        publisher = SingleQueueConusmerParamsGetter(queue_name).gen_publisher_for_faas()
        publisher.clear()

        return jsonify({
            "succ": True,
            "msg": f"Queue {queue_name} cleared successfully",
            "data": {
                "queue_name": queue_name,
                "success": True
            }
        })

    except Exception as e:
        logger.exception(f'Failed to clear queue: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to clear queue {queue_name if 'queue_name' in locals() else ''}: {str(e)}",
            "data": {
                "queue_name": queue_name if 'queue_name' in locals() else None,
                "success": False
            }
        }), 500



# ==================== Scheduled Task Management Endpoints ====================



@flask_blueprint.route("/get_one_queue_config", methods=['GET'])
def get_one_queue_config():
    """
    Get configuration info for a single queue.

    Query parameters:
        queue_name: Queue name (required)

    Returns:
        Queue configuration info, including function input parameter info (final_func_input_params_info)
    """
    try:
        queue_name = request.args.get('queue_name')

        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name parameter is required",
                "data": None
            }), 400

        queue_params = SingleQueueConusmerParamsGetter(queue_name).get_one_queue_params()

        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "data": queue_params
        })

    except Exception as e:
        logger.exception(f'Failed to get queue config: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get queue config: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/get_queues_config", methods=['GET'])
def get_queues_config():
    """
    Get configuration info for all queues.

    Returns detailed configuration parameters for all registered queues, including:
    - Queue name
    - Broker type
    - Concurrency count
    - QPS limit
    - Whether RPC mode is enabled
    - IMPORTANT: the consumer function's input parameter name list is in auto_generate_info.final_func_input_params_info
    - And all other parameters of the @boost decorator

    Mainly used for frontend visualization and management.
    """
    try:
        queues_config = QueuesConusmerParamsGetter().get_queues_params()

        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "data": {
                "queues_config": queues_config,
                "count": len(queues_config)
            }
        })
    except Exception as e:
        logger.exception(f'Failed to get queue config: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get queue config: {str(e)}",
            "data": {
                "queues_config": {},
                "count": 0
            }
        }), 500


@flask_blueprint.route("/get_queue_run_info", methods=['GET'])
def get_queue_run_info():
    """
    Get run info for a single queue.

    Query parameters:
        queue_name: Queue name (required)

    Returns:
        Detailed run info for the queue, including:
        - queue_params: Queue configuration parameters
        - active_consumers: List of active consumers
        - pause_flag: Pause flag (-1 or 0 means not paused, 1 means paused)
        - msg_num_in_broker: Number of messages in the broker (real-time)
        - history_run_count: Total historical run count
        - history_run_fail_count: Total historical failure count
        - all_consumers_last_x_s_execute_count: Execution count of all consumers across all consumer processes in the last X seconds
        - all_consumers_last_x_s_execute_count_fail: Failure count of all consumers across all consumer processes in the last X seconds
        - all_consumers_last_x_s_avarage_function_spend_time: Average function duration across all consumer processes in the last X seconds
        - all_consumers_avarage_function_spend_time_from_start: Average function duration across all consumer processes since start
        - all_consumers_total_consume_count_from_start: Total consumption count across all consumer processes since start
        - all_consumers_total_consume_count_from_start_fail: Total failure count across all consumer processes since start
        - all_consumers_last_execute_task_time: Timestamp of the last task executed across all consumer processes
    """
    try:
        queue_name = request.args.get('queue_name')

        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name parameter is required",
                "data": None
            }), 400

        # Get run info for a single queue
        queue_info = SingleQueueConusmerParamsGetter(queue_name).get_one_queue_params_and_active_consumers()

        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "data": queue_info
        })

    except Exception as e:
        logger.exception(f'Failed to get queue run info: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get queue run info: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/add_timing_job", methods=['POST'])
def add_timing_job():
    """
    Add a scheduled task.

    Supports three trigger types:
    1. date: Execute once at a specified date and time
       - Required: run_date
       - Example: {"trigger": "date", "run_date": "2025-12-03 15:00:00"}

    2. interval: Execute at a fixed time interval
       - Required: at least one of weeks, days, hours, minutes, seconds
       - Example: {"trigger": "interval", "seconds": 10}

    3. cron: Execute according to a cron expression
       - Required: at least one of year, month, day, week, day_of_week, hour, minute, second
       - Example: {"trigger": "cron", "hour": "*/2", "minute": "30"}

    Request body example:
    {
        "queue_name": "test_queue",
        "trigger": "interval",
        "seconds": 10,
        "job_id": "my_job_001",
        "job_store_kind": "redis",
        "replace_existing": false
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "succ": False,
                "msg": "Request body must be in JSON format",
                "data": None
            }), 400

        queue_name = data.get('queue_name')
        trigger = data.get('trigger')
        job_id = data.get('job_id')
        job_store_kind = data.get('job_store_kind', 'redis')
        replace_existing = data.get('replace_existing', False)

        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name field is required",
                "data": None
            }), 400

        if not trigger or trigger not in ['date', 'interval', 'cron']:
            return jsonify({
                "succ": False,
                "msg": "trigger field is required and must be one of 'date', 'interval', 'cron'",
                "data": None
            }), 400

        # Get job_adder
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)

        # print(888888,job_adder.aps_obj,id(job_adder.aps_obj),job_adder.aps_obj.get_jobs())

        # Build trigger arguments
        trigger_args = {}
        
        if trigger == 'date':
            if data.get('run_date'):
                trigger_args['run_date'] = data.get('run_date')
        
        elif trigger == 'interval':
            if data.get('weeks') is not None:
                trigger_args['weeks'] = data.get('weeks')
            if data.get('days') is not None:
                trigger_args['days'] = data.get('days')
            if data.get('hours') is not None:
                trigger_args['hours'] = data.get('hours')
            if data.get('minutes') is not None:
                trigger_args['minutes'] = data.get('minutes')
            if data.get('seconds') is not None:
                trigger_args['seconds'] = data.get('seconds')
        
        elif trigger == 'cron':
            if data.get('year') is not None:
                trigger_args['year'] = data.get('year')
            if data.get('month') is not None:
                trigger_args['month'] = data.get('month')
            if data.get('day') is not None:
                trigger_args['day'] = data.get('day')
            if data.get('week') is not None:
                trigger_args['week'] = data.get('week')
            if data.get('day_of_week') is not None:
                trigger_args['day_of_week'] = data.get('day_of_week')
            if data.get('hour') is not None:
                trigger_args['hour'] = data.get('hour')
            if data.get('minute') is not None:
                trigger_args['minute'] = data.get('minute')
            if data.get('second') is not None:
                trigger_args['second'] = data.get('second')
        
        # Add the job
        job = job_adder.add_push_job(
            trigger=trigger,
            args=data.get('args'),
            kwargs=data.get('kwargs'),
            id=job_id,
            replace_existing=replace_existing,
            **trigger_args
        )

        return jsonify({
            "succ": True,
            "msg": "Scheduled task added successfully",
            "data": {
                "job_id": job.id,
                "queue_name": queue_name,
                "trigger": str(job.trigger),
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                "status": "running",
                "kwargs": data.get('kwargs')
            }
        })

    except Exception as e:
        logger.exception(f'Failed to add scheduled task: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to add scheduled task: {str(e)}\n{traceback.format_exc()}",
            "data": None
        }), 500


@flask_blueprint.route("/get_timing_jobs", methods=['GET'])
def get_timing_jobs():
    """
    Get the list of scheduled tasks.

    Query parameters:
        queue_name: Queue name (optional; if not provided, returns tasks for all queues)
        job_store_kind: Job store type, 'redis' or 'memory', default 'redis'

    Return format:
        {
            "succ": True,
            "msg": "Retrieved successfully",
            "data": {
                "jobs_by_queue": {
                    "queue_name1": [job1, job2, ...],
                    "queue_name2": [job3, ...],
                    ...
                },
                "total_count": total task count
            }
        }
    """
    try:
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')

        # Store in dict format: {queue_name: [jobs]}
        jobs_by_queue = {}
        total_count = 0

        if queue_name:
            # Get tasks for the specified queue
            jobs_by_queue[queue_name] = []
            try:
                job_adder = gen_aps_job_adder(queue_name, job_store_kind)
                jobs = job_adder.aps_obj.get_jobs()

                for job in jobs:
                    # Determine task status: next_run_time is None means the task is paused
                    status = "paused" if job.next_run_time is None else "running"
                    # Get the kwargs of the task
                    kwargs = job.kwargs if hasattr(job, 'kwargs') and job.kwargs else {}
                    jobs_by_queue[queue_name].append({
                        "job_id": job.id,
                        "queue_name": queue_name,
                        "trigger": str(job.trigger),
                        "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                        "status": status,
                        "kwargs": kwargs
                    })
                    total_count += 1
            except Exception as e:
                logger.exception(f'Failed to get scheduled task list: {str(e)}')

        else:
            # Get tasks for all queues
            all_queues = list(QueuesConusmerParamsGetter().get_all_queue_names())
            for q_name in all_queues:
                jobs_by_queue[q_name] = []  # Initialize as empty array
                try:
                    job_adder = gen_aps_job_adder(q_name, job_store_kind)
                    jobs = job_adder.aps_obj.get_jobs()

                    for job in jobs:
                        # Determine task status: next_run_time is None means the task is paused
                        status = "paused" if job.next_run_time is None else "running"
                        # Get the kwargs of the task
                        kwargs = job.kwargs if hasattr(job, 'kwargs') and job.kwargs else {}
                        jobs_by_queue[q_name].append({
                            "job_id": job.id,
                            "queue_name": q_name,
                            "trigger": str(job.trigger),
                            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                            "status": status,
                            "kwargs": kwargs
                        })
                        total_count += 1
                except Exception as e:
                    logger.exception(f'Failed to get scheduled task list: {str(e)}')

        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "data": {
                "jobs_by_queue": jobs_by_queue,
                "total_count": total_count
            }
        })

    except Exception as e:
        logger.exception(f'Failed to get scheduled task list: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get scheduled task list: {str(e)}",
            "data": {
                "jobs_by_queue": {},
                "total_count": 0
            }
        }), 500


@flask_blueprint.route("/get_timing_job", methods=['GET'])
def get_timing_job():
    """
    Get detailed information for a single scheduled task.

    Query parameters:
        job_id: Job ID (required)
        queue_name: Queue name (required)
        job_store_kind: Job store type, 'redis' or 'memory', default 'redis'
    """
    try:
        job_id = request.args.get('job_id')
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')

        if not job_id or not queue_name:
            return jsonify({
                "succ": False,
                "msg": "job_id and queue_name parameters are required",
                "data": None
            }), 400

        job_adder = gen_aps_job_adder(queue_name, job_store_kind)

        # Get the specified job
        job = job_adder.aps_obj.get_job(job_id)

        if job:
            status = "paused" if job.next_run_time is None else "running"
            kwargs = job.kwargs if hasattr(job, 'kwargs') and job.kwargs else {}
            return jsonify({
                "succ": True,
                "msg": "Retrieved successfully",
                "data": {
                    "job_id": job.id,
                    "queue_name": queue_name,
                    "trigger": str(job.trigger),
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                    "status": status,
                    "kwargs": kwargs
                }
            })
        else:
            return jsonify({
                "succ": False,
                "msg": f"Job {job_id} does not exist",
                "data": None
            }), 404

    except Exception as e:
        logger.exception(f'Failed to get scheduled task: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get scheduled task: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/delete_timing_job", methods=['DELETE'])
def delete_timing_job():
    """
    Delete a scheduled task.

    Query parameters:
        job_id: Job ID (required)
        queue_name: Queue name (required)
        job_store_kind: Job store type, 'redis' or 'memory', default 'redis'
    """
    try:
        job_id = request.args.get('job_id')
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')

        if not job_id or not queue_name:
            return jsonify({
                "succ": False,
                "msg": "job_id and queue_name parameters are required",
                "data": None
            }), 400

        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.remove_job(job_id)

        return jsonify({
            "succ": True,
            "msg": f"Scheduled task {job_id} deleted successfully",
            "data": None
        })

    except Exception as e:
        logger.exception(f'Failed to delete scheduled task: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to delete scheduled task: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/delete_all_timing_jobs", methods=['DELETE'])
def delete_all_timing_jobs():
    """
    Delete all scheduled tasks.

    Query parameters:
        queue_name: Queue name (optional; if not provided, deletes all tasks for all queues)
        job_store_kind: Job store type, 'redis' or 'memory', default 'redis'
    """
    try:
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')
        
        deleted_count = 0
        failed_jobs = []
        
        if queue_name:
            # Delete all tasks for the specified queue
            try:
                job_adder = gen_aps_job_adder(queue_name, job_store_kind)
                jobs = job_adder.aps_obj.get_jobs()
                
                for job in jobs:
                    try:
                        job_adder.aps_obj.remove_job(job.id)
                        deleted_count += 1
                    except Exception as e:
                        failed_jobs.append(f"{job.id}: {str(e)}")
            except Exception as e:
                return jsonify({
                    "succ": False,
                    "msg": f"Failed to delete tasks for queue {queue_name}: {str(e)}",
                    "data": {
                        "deleted_count": deleted_count,
                        "failed_jobs": failed_jobs
                    }
                }), 500
        else:
            # Delete all tasks for all queues
            all_queues = list(QueuesConusmerParamsGetter().get_all_queue_names())
            for q_name in all_queues:
                try:
                    job_adder = gen_aps_job_adder(q_name, job_store_kind)
                    jobs = job_adder.aps_obj.get_jobs()

                    for job in jobs:
                        try:
                            job_adder.aps_obj.remove_job(job.id)
                            deleted_count += 1
                        except Exception as e:
                            failed_jobs.append(f"{q_name}/{job.id}: {str(e)}")
                except Exception as e:
                    logger.exception(f'Failed to delete tasks for queue {q_name}: {str(e)}')
                    # Queue has no tasks or error; continue to next queue

        return jsonify({
            "succ": True,
            "msg": f"Successfully deleted {deleted_count} scheduled tasks",
            "data": {
                "deleted_count": deleted_count,
                "failed_jobs": failed_jobs
            }
        })
        
    except Exception as e:
        logger.exception(f'Failed to delete all scheduled tasks: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to delete all scheduled tasks: {str(e)}",
            "data": {
                "deleted_count": 0,
                "failed_jobs": []
            }
        }), 500


@flask_blueprint.route("/pause_timing_job", methods=['POST'])
def pause_timing_job():
    """
    Pause a scheduled task.

    Query parameters:
        job_id: Job ID (required)
        queue_name: Queue name (required)
        job_store_kind: Job store type, 'redis' or 'memory', default 'redis'
    """
    try:
        job_id = request.args.get('job_id')
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')

        if not job_id or not queue_name:
            return jsonify({
                "succ": False,
                "msg": "job_id and queue_name parameters are required",
                "data": None
            }), 400

        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.pause_job(job_id)

        return jsonify({
            "succ": True,
            "msg": f"Scheduled task {job_id} paused",
            "data": None
        })

    except Exception as e:
        logger.exception(f'Failed to pause scheduled task: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to pause scheduled task: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/resume_timing_job", methods=['POST'])
def resume_timing_job():
    """
    Resume a scheduled task.

    Query parameters:
        job_id: Job ID (required)
        queue_name: Queue name (required)
        job_store_kind: Job store type, 'redis' or 'memory', default 'redis'
    """
    try:
        job_id = request.args.get('job_id')
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')

        if not job_id or not queue_name:
            return jsonify({
                "succ": False,
                "msg": "job_id and queue_name parameters are required",
                "data": None
            }), 400

        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.resume_job(job_id)

        return jsonify({
            "succ": True,
            "msg": f"Scheduled task {job_id} resumed",
            "data": None
        })

    except Exception as e:
        logger.exception(f'Failed to resume scheduled task: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to resume scheduled task: {str(e)}",
            "data": None
        }), 500

















@flask_blueprint.route("/get_scheduler_status", methods=['GET'])
def get_scheduler_status():
    """
    Get the scheduler status.

    Query parameters:
        queue_name: Queue name (required)
        job_store_kind: Job store type, 'redis' or 'memory', default 'redis'

    Returns:
        status: 0 (stopped), 1 (running), 2 (paused)
    """
    try:
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')

        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name parameter is required",
                "data": None
            }), 400

        job_adder = gen_aps_job_adder(queue_name, job_store_kind)

        state_map = {0: 'stopped', 1: 'running', 2: 'paused'}
        state = job_adder.aps_obj.state

        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "data": {
                "queue_name": queue_name,
                "status_code": state,
                "status_str": state_map.get(state, 'unknown')
            }
        })

    except Exception as e:
        logger.exception(f'Failed to get scheduler status: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get scheduler status: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/pause_scheduler", methods=['POST'])
def pause_scheduler():
    """
    Pause the scheduler.
    Note: This only pauses the scheduler instance in the current process. If multiple instances are deployed, each may need to be controlled separately.

    Query parameters:
        queue_name: Queue name (required)
        job_store_kind: Job store type, 'redis' or 'memory', default 'redis'
    """
    try:
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')

        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name parameter is required",
                "data": None
            }), 400

        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.pause()

        return jsonify({
            "succ": True,
            "msg": f"Scheduler paused ({queue_name})",
            "data": {
                "queue_name": queue_name,
                "status_str": "paused"
            }
        })

    except Exception as e:
        logger.exception(f'Failed to pause scheduler: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to pause scheduler: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/resume_scheduler", methods=['POST'])
def resume_scheduler():
    """
    Resume the scheduler.

    Query parameters:
        queue_name: Queue name (required)
        job_store_kind: Job store type, 'redis' or 'memory', default 'redis'
    """
    try:
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')

        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name parameter is required",
                "data": None
            }), 400

        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.resume()

        return jsonify({
            "succ": True,
            "msg": f"Scheduler resumed ({queue_name})",
            "data": {
                "queue_name": queue_name,
                "status_str": "running"
            }
        })

    except Exception as e:
        logger.exception(f'Failed to resume scheduler: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to resume scheduler: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/deprecate_queue", methods=['DELETE'])
def deprecate_queue():
    """
    Deprecate a queue - removes the queue name from the funboost_all_queue_names set and the project's queue list in Redis.

    Request body (JSON):
        {
            "queue_name": "name of the queue to deprecate"
        }

    Returns:
        {
            "succ": True/False,
            "msg": "message",
            "data": {
                "queue_name": "queue name",
                "removed": True/False
            }
        }
    """
    try:
        data = request.get_json()
        queue_name = data.get('queue_name')

        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "Missing parameter queue_name",
                "data": None
            }), 400

        # Call the deprecate_queue method of SingleQueueConusmerParamsGetter
        SingleQueueConusmerParamsGetter(queue_name).deprecate_queue()

        logger.info(f'Successfully deprecated queue: {queue_name}')
        return jsonify({
            "succ": True,
            "msg": f"Successfully deprecated queue: {queue_name}",
            "data": {
                "queue_name": queue_name,
                "removed": True
            }
        })

    except Exception as e:
        logger.exception(f'Failed to deprecate queue: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to deprecate queue: {str(e)}",
            "data": None
        }), 500


# ==================== care_project_name Project Filter Endpoints ====================

@flask_blueprint.route("/get_care_project_name", methods=['GET'])
def get_care_project_name():
    """
    Get the current care_project_name setting.

    Returns:
        {
            "succ": True,
            "msg": "Retrieved successfully",
            "data": {
                "care_project_name": "project name or None"
            }
        }
    """
    try:
        care_project_name = CareProjectNameEnv.get()

        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "data": {
                "care_project_name": care_project_name
            }
        })

    except Exception as e:
        logger.exception(f'Failed to get care_project_name: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/set_care_project_name", methods=['POST'])
def set_care_project_name():
    """
    Set care_project_name.

    Request body (JSON):
        {
            "care_project_name": "project name" or "" (empty string means no restriction)
        }

    Returns:
        {
            "succ": True,
            "msg": "Set successfully",
            "data": {
                "care_project_name": "the value after setting"
            }
        }
    """
    try:
        data = request.get_json()
        care_project_name = data.get('care_project_name', '')

        # Empty string means clear the restriction, set to empty string (in environment variable)
        CareProjectNameEnv.set(care_project_name)

        # If set to empty string, display as None when returning
        display_value = care_project_name if care_project_name else None

        logger.info(f'Set care_project_name to: {display_value}')
        return jsonify({
            "succ": True,
            "msg": f"Set successfully: {display_value if display_value else 'No restriction (show all)'}",
            "data": {
                "care_project_name": display_value
            }
        })

    except Exception as e:
        logger.exception(f'Failed to set care_project_name: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to set: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/get_all_project_names", methods=['GET'])
def get_all_project_names():
    """
    Get the list of all registered project names.

    Returns:
        {
            "succ": True,
            "msg": "Retrieved successfully",
            "data": {
                "project_names": ["project1", "project2", ...],
                "count": count
            }
        }
    """
    try:
        # Use QueuesConusmerParamsGetter to get all project names
        project_names = QueuesConusmerParamsGetter().get_all_project_names()

        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "data": {
                "project_names": sorted(project_names) if project_names else [],
                "count": len(project_names) if project_names else 0
            }
        })

    except Exception as e:
        logger.exception(f'Failed to get project name list: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get project name list: {str(e)}",
            "data": {
                "project_names": [],
                "count": 0
            }
        }), 500


# ==================== Running Consumer Info Endpoints ====================

@flask_blueprint.route("/running_consumer/hearbeat_info_by_queue_name", methods=['GET'])
def hearbeat_info_by_queue_name():
    """
    Get consumer heartbeat info by queue name.

    Query parameters:
        queue_name: Queue name (optional; if not provided or "All" is passed, returns all consumers)

    Returns:
        List of consumer heartbeat info
    """
    try:
        queue_name = request.args.get("queue_name")
        if queue_name in ("所有", None, ""):
            info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()
            ret_list = []
            for q_name, dic in info_map.items():
                ret_list.extend(dic)
            return jsonify({
                "succ": True,
                "msg": "Retrieved successfully",
                "data": ret_list
            })
        else:
            data = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_queue_name(queue_name)
            return jsonify({
                "succ": True,
                "msg": "Retrieved successfully",
                "data": data
            })
    except Exception as e:
        logger.exception(f'Failed to get consumer heartbeat info: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get consumer heartbeat info: {str(e)}",
            "data": []
        }), 500


@flask_blueprint.route("/running_consumer/hearbeat_info_by_ip", methods=['GET'])
def hearbeat_info_by_ip():
    """
    Get consumer heartbeat info by IP.

    Query parameters:
        ip: IP address (optional; if not provided or "All" is passed, returns all consumers)

    Returns:
        List of consumer heartbeat info
    """
    try:
        ip = request.args.get("ip")
        if ip in ("所有", None, ""):
            info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip()
            ret_list = []
            for q_name, dic in info_map.items():
                ret_list.extend(dic)
            return jsonify({
                "succ": True,
                "msg": "Retrieved successfully",
                "data": ret_list
            })
        else:
            data = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_ip(ip)
            return jsonify({
                "succ": True,
                "msg": "Retrieved successfully",
                "data": data
            })
    except Exception as e:
        logger.exception(f'Failed to get consumer heartbeat info: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get consumer heartbeat info: {str(e)}",
            "data": []
        }), 500


@flask_blueprint.route("/running_consumer/hearbeat_info_partion_by_queue_name", methods=['GET'])
def hearbeat_info_partion_by_queue_name():
    """
    Get consumer count grouped by queue name.

    Returns:
        List of queue names and consumer count per queue; the first item is "All" representing the total count.
    """
    try:
        info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()
        ret_list = []
        total_count = 0
        for k, v in info_map.items():
            ret_list.append({"collection_name": k, "count": len(v)})
            total_count += len(v)
        ret_list = sorted(ret_list, key=lambda x: x["collection_name"])
        ret_list.insert(0, {"collection_name": "所有", "count": total_count})
        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "data": ret_list
        })
    except Exception as e:
        logger.exception(f'Failed to get consumer group statistics: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get consumer group statistics: {str(e)}",
            "data": []
        }), 500


@flask_blueprint.route("/running_consumer/hearbeat_info_partion_by_ip", methods=['GET'])
def hearbeat_info_partion_by_ip():
    """
    Get consumer count grouped by IP.

    Returns:
        List of IP addresses and consumer count per IP; the first item is "All" representing the total count.
    """
    try:
        info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip()
        ret_list = []
        total_count = 0
        for k, v in info_map.items():
            ret_list.append({"collection_name": k, "count": len(v)})
            total_count += len(v)
        ret_list = sorted(ret_list, key=lambda x: x["collection_name"])
        ret_list.insert(0, {"collection_name": "所有", "count": total_count})
        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "data": ret_list
        })
    except Exception as e:
        logger.exception(f'Failed to get consumer group statistics: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get consumer group statistics: {str(e)}",
            "data": []
        }), 500


@flask_blueprint.route("/queues_params_and_active_consumers", methods=['GET'])
def get_queues_params_and_active_consumers():
    """
    Get configuration parameters and active consumer info for all queues.

    Returns:
        Configuration parameters and active consumer list for all queues.
    """
    try:
        data = QueuesConusmerParamsGetter().get_queues_params_and_active_consumers()
        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "data": data
        })
    except Exception as e:
        logger.exception(f'Failed to get queue params and active consumers: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get queue params and active consumers: {str(e)}",
            "data": {}
        }), 500


@flask_blueprint.route("/get_msg_num_all_queues", methods=['GET'])
def get_msg_num_all_queues():
    """
    Batch get message count for all queues.

    Notes:
        This is reported to Redis by consumers periodically every 10 seconds, so performance is good.
        No need to query each message queue in real-time; reads all queue message counts directly from Redis.

    Returns:
        {queue_name: msg_count, ...}
    """
    try:
        data = QueuesConusmerParamsGetter().get_msg_num(ignore_report_ts=True)
        return jsonify({
            "succ": True,
            "msg": "Retrieved successfully",
            "data": data
        })
    except Exception as e:
        logger.exception(f'Failed to get all queue message counts: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"Failed to get all queue message counts: {str(e)}",
            "data": {}
        }), 500


# Run the application (only create the app when run as the main script)
if __name__ == "__main__":
    from flask import Flask


    # This is an example showing how users can integrate flask_blueprint into their own app
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False
    app.register_blueprint(flask_blueprint)

    @app.route('/')
    def index():
        return "Funboost Flask API service is running!"

    print("Starting Funboost Flask API service...")
    print("Access URL: http://127.0.0.1:5000")

    app.run(host="0.0.0.0", port=5000, debug=True)
