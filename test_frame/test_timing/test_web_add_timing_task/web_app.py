# web_app.py
from flask import Flask, request, jsonify
from funboost import ApsJobAdder
from tasks import dynamic_task  # Import the task function so ApsJobAdder knows what to schedule

app = Flask(__name__)

# Create an ApsJobAdder instance.
# Key point: job_store_kind='redis' stores the scheduling plan in Redis,
# allowing the Web side and the background Worker side to share these plans.

# Start the scheduler in a paused state.
# This activates the connection to the backend job store (Redis), enabling management
# operations such as get_jobs/add_job/remove_job to work correctly,
# but it will not actually trigger any scheduled task executions.
job_adder = ApsJobAdder(dynamic_task, job_store_kind='redis', is_auto_paused=True,is_auto_start=True)



@app.route('/add_task', methods=['POST'])
def add_task():
    """Add a new periodic scheduled task"""
    data = request.json
    task_id = data.get('task_id')
    interval_seconds = data.get('interval_seconds', 10)
    message = data.get('message', 'default message')

    if not task_id:
        return jsonify({"error": "task_id is required"}), 400

    try:
        job_adder.add_push_job(
            trigger='interval',
            seconds=int(interval_seconds),
            id=str(task_id),
            replace_existing=True,
            kwargs={'task_id': task_id, 'message': message}
        )
        return jsonify({
            "status": "success",
            "message": f"Task '{task_id}' added, executing every {interval_seconds} seconds."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_tasks', methods=['GET'])
def get_tasks():
    """Get all scheduled tasks"""
    try:
        jobs = job_adder.aps_obj.get_jobs()
        job_list = [{
            "id": job.id,
            "next_run_time": str(job.next_run_time),
            "trigger": str(job.trigger)
        } for job in jobs]
        return jsonify(job_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/remove_task/<string:task_id>', methods=['DELETE'])
def remove_task(task_id: str):
    """Remove a specified scheduled task"""
    try:
        job_adder.aps_obj.remove_job(task_id)
        return jsonify({"status": "success", "message": f"Task '{task_id}' has been removed."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Start the Flask web server
    # In production, use Gunicorn or uWSGI instead
    app.run(host='0.0.0.0', port=5000, debug=True)
