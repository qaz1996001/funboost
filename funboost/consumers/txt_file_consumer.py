from pathlib import Path

from nb_filelock import FileLock
from persistqueue import Queue
import json
from persistqueue.serializers import json as json_serializer
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig


class TxtFileConsumer(AbstractConsumer, ):
    """
    Text file as message queue.
    Consumption confirmation is not implemented here. For consumption confirmation, please use the SQLITE_QUEUE or PERSISTQUEUE middleware.
    """

    def _dispatch_task(self):
        file_queue_path = str((Path(BrokerConnConfig.TXT_FILE_PATH) / self.queue_name).absolute())
        file_lock = FileLock(Path(file_queue_path) / f'_funboost_txtfile_{self.queue_name}.lock')
        queue = Queue(str((Path(BrokerConnConfig.TXT_FILE_PATH) / self.queue_name).absolute()), autosave=True, serializer=json_serializer)
        while True:
            with file_lock:
                item = queue.get()

                kw = {'body': item, 'q': queue, 'item': item}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass
        # kw['q'].task_done()

    def _requeue(self, kw):
        pass
        # kw['q'].nack(kw['item'])
