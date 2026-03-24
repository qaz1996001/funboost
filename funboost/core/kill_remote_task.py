import ctypes
import threading
import time
from funboost.utils.time_util import DatetimeConverter
from funboost.utils.redis_manager import RedisMixin
# import nb_log
from funboost.core.loggers import FunboostFileLoggerMixin
from funboost.core.current_task import FctContextThread


class ThreadKillAble(FctContextThread):
    task_id = None
    killed = False
    event_kill = threading.Event()


def kill_thread(thread_id):
    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))


class TaskHasKilledError(Exception):
    pass


def kill_fun_deco(task_id):
    def _inner(f):
        def __inner(*args, **kwargs):
            def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
                result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))
                threading.current_thread().event_kill.set()  # noqa

            result = []
            new_kwargs = {
                'oldfunc': f,
                'result': result,
                'oldfunc_args': args,
                'oldfunc_kwargs': kwargs
            }

            thd = ThreadKillAble(target=_new_func, args=(), kwargs=new_kwargs)
            thd.task_id = task_id
            thd.event_kill = threading.Event()
            thd.start()
            thd.event_kill.wait()
            if not result and thd.killed is True:
                raise TaskHasKilledError(f'{DatetimeConverter()} Thread has been killed {thd.task_id}')
            return result[0]

        return __inner

    return _inner


def kill_thread_by_task_id(task_id):
    for t in threading.enumerate():
        if isinstance(t, ThreadKillAble):
            thread_task_id = getattr(t, 'task_id', None)
            if thread_task_id == task_id:
                t.killed = True
                t.event_kill.set()
                kill_thread(t.ident)


kill_task = kill_thread_by_task_id


class RemoteTaskKillerZset(RedisMixin, FunboostFileLoggerMixin):
    """
    Implemented using zset, requires multiple zrank calls.
    """

    def __init__(self, queue_name, task_id):
        self.queue_name = queue_name
        self.task_id = task_id
        self._redis_zset_key = f'funboost_kill_task:{queue_name}'
        self._lsat_kill_task_ts = time.time()

    def send_remote_task_comd(self):
        self.redis_db_frame.zadd(self._redis_zset_key, {self.task_id: time.time()})

    def judge_need_revoke_run(self):
        if self.redis_db_frame.zrank(self._redis_zset_key, self.task_id) is not None:
            self.redis_db_frame.zrem(self._redis_zset_key, self.task_id)
            return True
        return False

    def kill_local_task(self):
        kill_task(self.task_id)

    def start_cycle_kill_task(self):
        def _start_cycle_kill_task():
            while 1:
                for t in threading.enumerate():
                    if isinstance(t, ThreadKillAble):
                        thread_task_id = getattr(t, 'task_id', None)
                        if self.redis_db_frame.zrank(self._redis_zset_key, thread_task_id) is not None:
                            self.redis_db_frame.zrem(self._redis_zset_key, thread_task_id)
                            t.killed = True
                            t.event_kill.set()
                            kill_thread(t.ident)
                            self._lsat_kill_task_ts = time.time()
                            self.logger.warning(f'Task {thread_task_id} in queue {self.queue_name} has been killed')
                if time.time() - self._lsat_kill_task_ts < 2:
                    time.sleep(0.001)
                else:
                    time.sleep(5)

        threading.Thread(target=_start_cycle_kill_task).start()


class RemoteTaskKiller(RedisMixin, FunboostFileLoggerMixin):
    """
    Implemented using hash, only requires one hmget call.
    """

    def __init__(self, queue_name, task_id):
        self.queue_name = queue_name
        self.task_id = task_id
        # self.redis_zset_key = f'funboost_kill_task:{queue_name}'
        self._redis_hash_key = f'funboost_kill_task_hash:{queue_name}'
        # self._lsat_kill_task_ts = 0  # time.time()
        self._recent_scan_need_kill_task = False

    def send_kill_remote_task_comd(self):
        # self.redis_db_frame.zadd(self.redis_zset_key, {self.task_id: time.time()})
        self.redis_db_frame.hset(self._redis_hash_key, key=self.task_id, value=time.time())

    def judge_need_revoke_run(self):
        if self.redis_db_frame.hexists(self._redis_hash_key, self.task_id):
            self.redis_db_frame.hdel(self._redis_hash_key, self.task_id)
            return True
        return False

    def kill_local_task(self):
        kill_task(self.task_id)

    def start_cycle_kill_task(self):
        def _start_cycle_kill_task():
            while 1:
                if self._recent_scan_need_kill_task:
                    # print(0.0001)
                    time.sleep(0.01)
                else:
                    # print(555)
                    time.sleep(5)
                self._recent_scan_need_kill_task = False
                thread_task_id_list = []
                task_id__thread_map = {}
                for t in threading.enumerate():
                    if isinstance(t, ThreadKillAble):
                        thread_task_id = getattr(t, 'task_id', None)
                        thread_task_id_list.append(thread_task_id)
                        task_id__thread_map[thread_task_id] = t
                if thread_task_id_list:
                    values = self.redis_db_frame.hmget(self._redis_hash_key, keys=thread_task_id_list)
                    for idx, thread_task_id in enumerate(thread_task_id_list):
                        if values[idx] is not None:
                            self.redis_db_frame.hdel(self._redis_hash_key, thread_task_id)
                            t = task_id__thread_map[thread_task_id]
                            t.killed = True
                            t.event_kill.set()
                            kill_thread(t.ident)
                            self._recent_scan_need_kill_task = True
                            self.logger.warning(f'Task {thread_task_id} in queue {self.queue_name} has been killed')

        threading.Thread(target=_start_cycle_kill_task).start()


if __name__ == '__main__':

    test_lock = threading.Lock()


    def my_fun(x):
        """
        Using lock.acquire(), force-killing will permanently prevent the lock from being released.
        """
        test_lock.acquire()
        print(f'start {x}')
        # resp = requests.get('http://127.0.0.1:5000')  # flask interface sleeps for 30 seconds,
        # print(resp.text)
        for i in range(10):
            time.sleep(2)
        test_lock.release()
        print(f'over {x}')
        return 666


    def my_fun2(x):
        """
        Using with lock, force-killing will not cause the lock to be permanently unreleased.
        """
        with test_lock:
            print(f'start {x}')
            # resp = requests.get('http://127.0.0.1:5000')  # flask interface sleeps for 30 seconds,
            # print(resp.text)
            for i in range(10):
                time.sleep(2)
            print(f'over {x}')
            return 666


    threading.Thread(target=kill_fun_deco(task_id='task1234')(my_fun2), args=(777,)).start()
    threading.Thread(target=kill_fun_deco(task_id='task5678')(my_fun2), args=(888,)).start()
    time.sleep(5)
    # kill_thread_by_task_id('task1234')

    k = RemoteTaskKiller('test_kill_queue', 'task1234')
    k.start_cycle_kill_task()
    k.send_kill_remote_task_comd()

    """
    First pattern:
    test_lock.acquire()
    execute time-consuming IO code
    test_lock.release()
    If lock.acquire() is used to acquire the lock, and the thread is force-killed while executing the time-consuming code
    before lock.release() is called, the lock will never be released.

    Second pattern:
    with test_lock:
        execute time-consuming IO code
    If 'with lock' is used to acquire the lock, and the thread is force-killed while executing the time-consuming code,
    the lock will NOT be permanently unreleased.

    """
