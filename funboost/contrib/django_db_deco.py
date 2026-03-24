from django.db import close_old_connections


def close_old_connections_deco(f):
    """
    If the consuming function needs to operate Django ORM, please set consuming_function_decorator=close_old_connections_deco
    @boost(BoosterParams(queue_name='create_student_queue',
                         broker_kind=BrokerEnum.REDIS_ACK_ABLE,
                         consuming_function_decorator=close_old_connections_deco, # If "gone away" errors persist, add this decorator. django_celery and django-apscheduler also call close_old_connections in their source code.

                         )
           )
    """

    def _inner(*args, **kwargs):
        close_old_connections()
        try:
            result = f(*args, **kwargs)
        finally:
            close_old_connections()

        return result

    return _inner
