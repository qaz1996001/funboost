


from funboost.funweb.app import (
    start_funboost_web_manager,
    app,
    CareProjectNameEnv,
    QueuesConusmerParamsGetter,
)



CareProjectNameEnv.set('test_project1')


a=4

if __name__ == '__main__':
    QueuesConusmerParamsGetter().cycle_get_queues_params_and_active_consumers_and_report(daemon=True)
    # Disable use_reloader, use external watchdog reloader (flask_realod.py)
    app.run(debug=True, use_reloader=False, threaded=True, host='0.0.0.0', port=27011)
    
    """
    Auto-restart Flask via test_frame/test_watchdog_broker/flask_realod.py

    The built-in use_reloader often restarts while code is being edited, causing errors
    that prevent subsequent auto-restart and recovery.
    """


   
