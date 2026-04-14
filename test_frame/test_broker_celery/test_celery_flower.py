from funboost.consumers.celery_consumer import CeleryHelper

CeleryHelper.start_flower(port=5557)  # Start flower web UI; this function can also be started in a separate script