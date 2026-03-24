import queue


class PythonQueues:
    local_pyhton_queue_name__local_pyhton_queue_obj_map  = {}

    @classmethod
    def get_queue(cls, queue_name, maxsize=0):
        """
        Get or create an in-memory queue

        :param queue_name: Queue name
        :param maxsize: Maximum queue capacity, 0 means unbounded queue (default), positive integer means bounded queue.
                       When the queue is full, put operations will block until space is available.
        :return: queue.Queue object
        """
        if queue_name not in cls.local_pyhton_queue_name__local_pyhton_queue_obj_map:
            cls.local_pyhton_queue_name__local_pyhton_queue_obj_map[queue_name] = queue.Queue(maxsize=maxsize)
        return cls.local_pyhton_queue_name__local_pyhton_queue_obj_map[queue_name]

