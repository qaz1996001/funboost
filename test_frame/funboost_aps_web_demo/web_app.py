from flask import Flask
from funboost import ApsJobAdder
from funcs import fun_sum

app = Flask(__name__)

@app.route('/', methods=['get'])
def index():
    return 'Demonstrate adding funboost scheduled tasks'

@app.route('/add_job', methods=['get'])
def api_add_job():
    """
    Add apscheduler scheduled tasks via API, using redis as jobstores. is_auto_paused=True means pausing aps from executing tasks,
    because here we only need to add/delete/modify/query scheduled tasks in redis, not actually execute them.

    You can also use is_auto_paused=False, so the aps object will both add scheduled tasks to redis and execute tasks in redis.
    Because funboost's apscheduler is customized and uses redis distributed locks when scanning scheduled tasks,
    you don't need to worry about duplicate scheduled task executions when starting the apscheduler object multiple times.
    """
    ApsJobAdder(fun_sum,job_store_kind='redis',is_auto_paused=True).add_push_job(
        args=(1, 2),
        trigger='interval',  # Use interval trigger
        seconds=10,
        id='add_numbers_job', # Task ID
        replace_existing=True,
        name='add_numbers_job',
    )
    return 'ok'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009)
