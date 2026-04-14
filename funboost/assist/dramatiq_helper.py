import argparse
from funboost.core.loggers import FunboostMetaTypeFileLogger
import dramatiq
from dramatiq.cli import main
from funboost.funboost_config_deafult import BrokerConnConfig
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.rabbitmq import RabbitmqBroker

if BrokerConnConfig.DRAMATIQ_URL.startswith('redis'):
    broker = RedisBroker(url=BrokerConnConfig.DRAMATIQ_URL)
elif BrokerConnConfig.DRAMATIQ_URL.startswith('amqp'):
    broker = RabbitmqBroker(url=BrokerConnConfig.DRAMATIQ_URL)
else:
    raise ValueError('DRAMATIQ_URL configuration error, it needs to be configured as a URL connection string, e.g. amqp://rabbitmq_user:rabbitmq_pass@127.0.0.1:5672/ or redis://:passwd@192.168.64.151:6378/7 ')
dramatiq.set_broker(broker)

"""
 {'max_age', 'throws', 'pipe_target', 'pipe_ignore', 'on_success', 'retry_when', 'time_limit', 'min_backoff', 'max_retries', 'max_backoff', 'notify_shutdown', 'on_failure'}
"""


class DramatiqHelper(metaclass=FunboostMetaTypeFileLogger):

    broker = dramatiq.get_broker()
    to_be_start_work_celery_queue_name_set = set()  # Stores queue names that need to be run by the worker.

    queue_name__actor_map = {}

    @classmethod
    def realy_start_dramatiq_worker(cls):
        p = argparse.ArgumentParser()
        pa = p.parse_args()

        pa.broker = 'funboost.assist.dramatiq_helper'
        pa.modules = []
        pa.processes = 1
        pa.threads = 200
        pa.path = ''
        pa.queues = list(cls.to_be_start_work_celery_queue_name_set)
        pa.log_file = None
        pa.skip_logging = False
        pa.use_spawn = False
        pa.forks = []
        pa.worker_shutdown_timeout = 600000
        pa.verbose = 0
        pa.pid_file = None

        cls.logger.warning(f'dramatiq command line startup parameters {pa}')
        main(pa)


'''
Namespace(broker='test_dramatiq_raw', modules=[], processes=1, threads=8, path='.', queues=None, pid_file=None, log_file=None, skip_logging=False, use_spawn=False, forks=[], worker_shutdown_timeout=600000, verbose=0)
python -m dramatiq test_dramatiq_raw -p 1
'''
