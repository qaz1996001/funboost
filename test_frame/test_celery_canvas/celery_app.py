import os
import warnings
from celery import Celery


def make_celery() -> Celery:
    """Create a Celery application (supports fallback to eager in-process execution when no broker is available).

    Environment variables:
    - CELERY_BROKER_URL: e.g. `redis://127.0.0.1:6379/0` or `pyamqp://guest@localhost//`
    - CELERY_RESULT_BACKEND: e.g. `redis://127.0.0.1:6379/0` or `rpc://`
    """

    broker_url = os.getenv("CELERY_BROKER_URL", "").strip()
    result_backend = os.getenv("CELERY_RESULT_BACKEND", "").strip()

    app = Celery("test_celery_canvas")

    if not broker_url:
        # No external broker: fall back to single-process eager mode for quick experimentation
        warnings.warn(
            "CELERY_BROKER_URL not detected; task_always_eager mode enabled (single-process local execution).\n"
            "For true distributed concurrency and monitoring, set a Redis/RabbitMQ broker and start a worker.",
            RuntimeWarning,
        )
        app.conf.update(
            broker_url="memory://",
            result_backend="cache+memory://",
            task_always_eager=True,
            task_eager_propagates=True,
            task_ignore_result=False,
        )
    else:
        if not result_backend:
            if broker_url.startswith("redis://"):
                result_backend = broker_url
            else:
                # Default to RPC result backend (requires AMQP)
                result_backend = "rpc://"
        app.conf.update(
            broker_url=broker_url,
            result_backend=result_backend,
            task_always_eager=False,
        )

    app.conf.update(
        timezone="Asia/Shanghai",
        enable_utc=False,
        task_acks_late=True,
        worker_hijack_root_logger=False,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        result_expires=3600,
        task_default_queue="canvas_default",
        task_routes={
            "test_frame.test_celery_canvas.tasks.fetch_url": {"queue": "io"},
            "test_frame.test_celery_canvas.tasks.sleep_task": {"queue": "io"},
            "test_frame.test_celery_canvas.tasks.retryable_task": {"queue": "cpu"},
        },
        task_annotations={
            "test_frame.test_celery_canvas.tasks.rate_limited_task": {"rate_limit": "10/m"}
        },
    )

    # Auto-discover tasks
    app.autodiscover_tasks(["test_frame.test_celery_canvas"])
    return app


app = make_celery()


