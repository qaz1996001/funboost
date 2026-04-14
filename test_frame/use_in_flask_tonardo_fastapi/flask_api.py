import flask
from flask_mail import Mail, Message
from funboost import boost, BrokerEnum, TaskOptions
from funboost.publishers.base_publisher import AsyncResult

app = flask.Flask(__name__)

app.config.update(
    MAIL_SERVER='MAIL_SERVER',
    MAIL_PORT=678,
    MAIL_USE_TLS=True,
    MAIL_USEERNAME='MAIL_USERNAME',
    MAIL_PASSWORD='MAIL_PASSWORD',
    MAIL_DEFAULT_SENDER=('Grey Li', 'MAIL_USERNAME')
)

mail = Mail(app)


@boost(queue_name='flask_test_queue', broker_kind=BrokerEnum.REDIS)
def send_email(msg):
    """
    Demonstrates general tasks where the function does not need Flask's app context.
    :param msg:
    :return:
    """
    print(f'Sending email  {msg}')


@boost(queue_name='flask_test_queue', broker_kind=BrokerEnum.REDIS)
def send_main_with_app_context(msg):
    """
    Demonstrates use of flask_mail, which requires the Flask app context.
    :param msg:
    :return:
    """
    with app.app_context():
        # The Message class needs to read mail sender and other info from Flask config.
        # Since publishing and consuming may be on different machines or processes,
        # the app context must be used to access the mail configuration.
        message = Message(subject='title', recipients=['367224698@qq.com'], body=msg)
        mail.send(message)



#############################  Optional: wrap with a generic context decorator — start  ################################

def your_app_context_deco(flask_appx: flask.Flask):
    def _deco(fun):
        def __deco(*args, **kwargs):
            with flask_appx.app_context():
                return fun(*args, **kwargs)

        return _deco

    return _deco


@boost(queue_name='flask_test_queue', broker_kind=BrokerEnum.REDIS,consuming_function_decorator=your_app_context_deco(app))
def send_main_with_app_context2(msg):
    """
    Demonstrates use of flask_mail, which requires the Flask app context.
    :param msg:
    :return:
    """
    message = Message(subject='title', recipients=['367224698@qq.com'], body=msg)
    mail.send(message)

#############################  Optional: wrap with a generic context decorator — end  ################################


# This is a Flask route; it publishes tasks to the message queue from within the route handler.
@app.route('/')
def send_email_api():
    """
    :return:
    """
    # If the frontend doesn't care about the result and just wants to push the task to the middleware,
    # use send_email.push(msg='email content').
    async_result = send_email.publish(dict(msg='email content'), task_options=TaskOptions(is_using_rpc_mode=True))  # type: AsyncResult
    return async_result.task_id
    # return async_result.result  # Not recommended; this blocks the route.
    # The better approach is to write a separate Ajax endpoint that fetches the result using the task_id.
    # The backend implementation uses RedisAsyncResult(task_id, timeout=30).result.

    # If you need the result, the best approach is not Ajax polling; using MQTT is the best solution.
    # The frontend subscribes to an MQTT topic, and the consumer function publishes the result to that topic.
    # This approach is far simpler than importing a pile of WebSocket-related modules on the backend,
    # offers great performance (a single MQTT broker supports hundreds of thousands of persistent connections),
    # and is far more real-time than Ajax polling.


if __name__ == '__main__':
    app.run()
