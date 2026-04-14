from __future__ import annotations
import copy
import inspect
from multiprocessing import Process
import os
import sys
import types
import typing
import threading
from funboost.concurrent_pool import FlexibleThreadPool
from funboost.concurrent_pool.async_helper import simple_run_in_executor
from funboost.constant import FunctionKind, StrConst
from funboost.utils.class_utils import ClsHelper

from funboost.utils.ctrl_c_end import ctrl_c_recv
from funboost.core.loggers import flogger, develop_logger, logger_prompt

from functools import wraps

from funboost.core.exceptions import BoostDecoParamsIsOldVersion
from funboost.core.func_params_model import (
    BoosterParams,
    FunctionResultStatusPersistanceConfig,
    TaskOptions,
    PublisherParams,
)

from funboost.factories.consumer_factory import get_consumer, ConsumerCacheProxy
from funboost.factories.publisher_factotry import get_publisher, PublisherCacheProxy

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.base_publisher import AbstractPublisher


from funboost.core.msg_result_getter import AsyncResult, AioAsyncResult


class Booster:
    """
    funboost places great emphasis on code auto-completion in PyCharm. Metaprogramming often makes auto-completion difficult in PyCharm.
    This __call__ approach enables auto-completion for both the consuming function's push/consume methods and the function's own parameters in PyCharm - a two-in-one benefit. Auto-completion is very important.
    After a function `fun` is decorated with the `boost` decorator, isinstance(fun, Booster) returns True.

    For pydantic PyCharm code auto-completion, install the pydantic plugin: PyCharm -> File -> Settings -> Plugins -> search for "pydantic" and install it.

    Booster combines Consumer and Publisher methods into a single entity.
    """


    def __init__(
        self,
        queue_name: typing.Union[BoosterParams, str] = None,
        *,
        boost_params: BoosterParams = None,
        **kwargs,
    ):
        """
        @boost is the most important function in the funboost framework. You must understand the parameters in BoosterParams.
        It is recommended to always use @boost(BoosterParams(queue_name='queue_test_f01', qps=0.2, )) style parameter passing.


        For pydantic PyCharm code auto-completion, install the pydantic plugin: PyCharm -> File -> Settings -> Plugins -> search for "pydantic" and install it.
        (Newer versions of PyCharm have built-in pydantic support for auto-completion, showing how excellent pydantic is.)

        It is strongly recommended to put all parameters in BoosterParams(), not pass them directly outside BoosterParams. The old direct parameter passing in @boost is still supported for backward compatibility.
        It is recommended to always pass a BoosterParams type instead of a string for the first parameter queue_name, e.g. @boost(BoosterParams(queue_name='queue_test_f01', qps=0.2, ))


        ```python
        # @boost('queue_test_f01', qps=0.2, ) # old parameter style
        @boost(BoosterParams(queue_name='queue_test_f01', qps=0.2, )) # new parameter style, all params in the popular pydantic model BoosterParams.
        def f(a, b):
            print(a + b)

        for i in range(10, 20):
            f.pub(dict(a=i, b=i * 2))
            f.push(i, i * 2)
        f.consume()
        # f.multi_process_conusme(8)             # This is a newly added method, fine-grained thread/coroutine concurrency combined with 8 processes, blazing fast.
        ```


        @boost('queue_test_f01', qps=0.2, )
        @boost(BoosterParams(queue_name='queue_test_f01', qps=0.2, ))
        @Booster(BoosterParams(queue_name='queue_test_f01', qps=0.2, ))
        @BoosterParams(queue_name='queue_test_f01', qps=0.2, )
        The above 4 forms are equivalent.
        """

        # The following code is complex, mainly for backward compatibility with the old direct parameter passing in @boost. It is strongly recommended to use the new parameter style with all params in a single BoosterParams, then you don't need to worry about the logic below.
        if isinstance(queue_name, str):
            if boost_params is None:
                boost_params = BoosterParams(queue_name=queue_name)
        elif queue_name is None and boost_params is None:
            raise ValueError("Invalid boost parameters")
        elif isinstance(queue_name, BoosterParams):
            boost_params = queue_name
        if isinstance(queue_name, str) or kwargs:
            flogger.warning(
                f"""Your queue {queue_name}, since funboost version 40.0: {BoostDecoParamsIsOldVersion.default_message}"""
            )
        boost_params_merge = boost_params.copy()
        boost_params_merge.update_from_dict(kwargs)
        self.boost_params: BoosterParams = boost_params_merge
        self.queue_name = boost_params_merge.queue_name

    def __str__(self):
        return f"{type(self)}  queue: {self.queue_name} function: {self.consuming_function} booster"

    def __get__(self, instance, cls):
        """https://python3-cookbook.readthedocs.io/zh_CN/latest/c09/p09_define_decorators_as_classes.html"""
        if instance is None:
            return self
        else:
            return types.MethodType(self, instance)

    def __call__(self, *args, **kwargs) -> Booster:
        """
        # The first call to __call__ decorates the function and returns a Booster object. From then on, the consuming function becomes a Booster type object.
        # How does a Booster type object support the original direct function execution? By going to the else branch, directly using self.consuming_function to run with the parameters.
        # This is a very clever design.
        # If the user later decides not to use funboost's distributed function scheduling, they can run the function directly as before without removing the @boost decorator.
        """
        if (
            len(kwargs) == 0
            and len(args) == 1
            and isinstance(args[0], typing.Callable)
            and not isinstance(args[0], Booster)
        ):
            consuming_function = args[0]
            self.boost_params.consuming_function = consuming_function
            self.boost_params.consuming_function_raw = consuming_function
            self.boost_params.consuming_function_name = consuming_function.__name__
            # print(consuming_function)
            # print(ClsHelper.get_method_kind(consuming_function))
            # print(inspect.getsourcelines(consuming_function))
            if self.boost_params.consuming_function_kind is None:
                self.boost_params.consuming_function_kind = ClsHelper.get_method_kind(
                    consuming_function
                )
            # if self.boost_params.consuming_function_kind in [FunctionKind.CLASS_METHOD,FunctionKind.INSTANCE_METHOD]:
            #     if self.boost_params.consuming_function_class_module is None:
            #         self.boost_params.consuming_function_class_module = consuming_function.__module__
            #     if self.boost_params.consuming_function_class_name is None:
            #         self.boost_params.consuming_function_class_name = consuming_function.__qualname__.split('.')[0]
            logger_prompt.debug(
                f""" {self.boost_params.queue_name} booster configuration is {self.boost_params.json_str_value()}"""
            )
            self.consuming_function = consuming_function
            self.is_decorated_as_consume_function = True

            consumer: AbstractConsumer = ConsumerCacheProxy(
                self.boost_params
            ).consumer
            self.consumer = consumer

            self.publisher: AbstractPublisher = consumer.publisher_of_same_queue
            # self.publish = self.pub = self.apply_async = consumer.publisher_of_same_queue.publish
            # self.push = self.delay = consumer.publisher_of_same_queue.push
            self.publish = self.pub = self.apply_async = self.publisher.publish
            self.aio_publish = self.publisher.aio_publish
            self.push = self.delay = self.publisher.push
            self.aio_push = self.publisher.aio_push

            self.clear = self.clear_queue = consumer.publisher_of_same_queue.clear
            self.get_message_count = consumer.publisher_of_same_queue.get_message_count

            self.start_consuming_message = self.consume = self.start = (
                consumer.start_consuming_message
            ) # consume runs in a foreground thread, non-blocking
            self.clear_filter_tasks = consumer.clear_filter_tasks
            self.wait_for_possible_has_finish_all_tasks = (
                consumer.wait_for_possible_has_finish_all_tasks
            )

            self.pause = self.pause_consume = consumer.pause_consume
            self.continue_consume = consumer.continue_consume

            wraps(consuming_function)(self)

            BoosterRegistry(self.boost_params.booster_registry_name).regist_booster(self)
            
            return self
        else:
            return self.consuming_function(*args, **kwargs)

    # noinspection PyMethodMayBeStatic
    def multi_process_consume(self, process_num=1):
        """Ultra-fast multi-process consuming"""
        from funboost.core.muliti_process_enhance import run_consumer_with_multi_process

        run_consumer_with_multi_process(self, process_num)

    multi_process_start = multi_process_consume
    mp_consume = multi_process_consume

    # noinspection PyMethodMayBeStatic
    def multi_process_pub_params_list(self, params_list, process_num=16):
        """Ultra-fast multi-process publishing, e.g. quickly publish 10 million tasks to the broker, then consume them later"""
        """
        Usage example: quickly publish 10 million tasks using 20 processes, fully utilizing multi-core CPUs.
        @boost('test_queue66c', qps=1/30,broker_kind=BrokerEnum.KAFKA_CONFLUENT)
        def f(x, y):
            print(f'Function execution start time {time.strftime("%H:%M:%S")}')
        if __name__ == '__main__':
            f.multi_process_pub_params_list([{'x':i,'y':i*3}  for i in range(10000000)],process_num=20)
            f.consume()
        """
        from funboost.core.muliti_process_enhance import multi_process_pub_params_list

        multi_process_pub_params_list(self, params_list, process_num)

    # noinspection PyDefaultArgument
    # noinspection PyMethodMayBeStatic
    def fabric_deploy(
        self,
        host,
        port,
        user,
        password,
        path_pattern_exluded_tuple=("/.git/", "/.idea/", "/dist/", "/build/"),
        file_suffix_tuple_exluded=(".pyc", ".log", ".gz"),
        only_upload_within_the_last_modify_time=3650 * 24 * 60 * 60,
        file_volume_limit=1000 * 1000,
        sftp_log_level=20,
        extra_shell_str="",
        invoke_runner_kwargs={"hide": None, "pty": True, "warn": False},
        python_interpreter="python3",
        process_num=1,
        pkey_file_path=None,
    ):
        """
        See fabric_deploy function for parameter details. Parameters are repeated here for PyCharm auto-completion.
        """
        params = copy.copy(locals())
        params.pop("self")
        from funboost.core.fabric_deploy_helper import fabric_deploy

        fabric_deploy(self, **params)

    def __getstate__(self):
        state = {}
        state["queue_name"] = self.boost_params.queue_name
        state["booster_registry_name"] = self.boost_params.booster_registry_name
        return state

    def __setstate__(self, state):
        """Advanced technique supporting pickle serialization and deserialization of booster objects, a very clever design.
        This allows aps_obj.add_job(booster.push,...) to work properly when using redis as apscheduler's jobstores,
        avoiding errors about booster objects being unable to be pickled.

        This deserialization doesn't try to serialize socket/threading.Lock directly, but bypasses the problem using identity-based proxy deserialization.
        """
        cur_boosters_manager = BoosterRegistry(
            state["booster_registry_name"]
        )
        _booster = cur_boosters_manager.get_or_create_booster_by_queue_name(
            state["queue_name"]
        )
        self.__dict__.update(_booster.__dict__)


boost = Booster  # @boost for consuming functions. If auto-completion doesn't work, use Booster directly. Some PyCharm 2024 versions have issues with auto-completing .consume .push methods on @boost decorated functions.
task_deco = boost  # Both decorator names work. task_deco is the original name, kept for backward compatibility.


def gen_pid_queue_name_key(queue_name: str,) -> typing.Tuple[int, str]:
    pid = os.getpid()
    return (pid,  queue_name)

class BoosterRegistry:
    """
    Manages boosters, allowing one-click startup of multiple consuming functions or a group of consuming functions.

    BoosterRegistry was added later. The original BoostersManager class contained multiple classmethods with the same method names and parameters.
    For backward compatibility with BoostersManager usage, the current BoostersManager is an instance of BoosterRegistry.

    Uses __new__ to implement the flyweight pattern, each booster_registry_name corresponds to a unique instance.
    """

    _lock = threading.Lock()
    _instances: typing.Dict[str, 'BoosterRegistry'] = {}  # Flyweight pattern cache

    def __new__(cls, booster_registry_name: str):
        # Check cache first (no lock, high performance)
        if booster_registry_name not in cls._instances:
            with cls._lock:
                # Double-Checked Locking
                if booster_registry_name not in cls._instances:
                    instance = super().__new__(cls)
                    instance._initialize(booster_registry_name)
                    cls._instances[booster_registry_name] = instance
        return cls._instances[booster_registry_name]

    def __init__(self, booster_registry_name: str):
        # __new__ has already handled all initialization logic, keep this empty
        pass

    def _initialize(self, booster_registry_name: str):
        """Actual initialization logic, called only once in __new__"""
        self.booster_registry_name = booster_registry_name

        # pid_queue_name__booster_map stores {(process_id, queue_name): Booster object}
        self.pid_queue_name__booster_map: typing.Dict[
            typing.Tuple[int, str], Booster
        ] = {}

        # queue_name__boost_params_map stores {queue_name: BoosterParams}
        self.queue_name__boost_params_map: typing.Dict[str, BoosterParams] = {}

        self.pid_queue_name__has_start_consume_set = set()

      

    def regist_booster(self, booster: Booster):
        """This is automatically called by the framework during @boost decoration, no need for users to call it manually"""
        # if booster.boost_params.is_fake_booster is True:
        #     return
        self.pid_queue_name__booster_map[
            gen_pid_queue_name_key(booster.boost_params.queue_name)
        ] = booster
        self.queue_name__boost_params_map[booster.boost_params.queue_name] = (
            booster.boost_params
        )

    def show_all_boosters(self):
        queues = []
        for pid_queue_name, booster in self.pid_queue_name__booster_map.items():
            queues.append(pid_queue_name[1])
            flogger.debug(f"booster: {pid_queue_name[1]}  {booster}")

    def get_all_queues(self) -> list[str]:
        return list(self.queue_name__boost_params_map.keys())

    def get_all_boosters(self) -> list[Booster]:
        return [self.get_or_create_booster_by_queue_name(q) for q in self.get_all_queues()]

    def get_all_queue_name__boost_params_unstrict_dict(self):
        """
        Mainly used for frontend or visualization display.

        Returns a dict where keys are queue names and values are @boost BoosterParams parameter dicts.
        Some BoosterParams parameters are complex object types that cannot be JSON serialized.
        """
        return {
            k: v.get_str_dict() for k, v in self.queue_name__boost_params_map.items()
        }

    def get_booster(self, queue_name: str) -> Booster:
        """
        Get booster object in current process. Note the difference from get_or_create_booster_by_queue_name below, mainly relevant when using multi-process.
        :param queue_name:
        :return:
        """

        key = gen_pid_queue_name_key(queue_name)
        if key in self.pid_queue_name__booster_map:
            return self.pid_queue_name__booster_map[key]
        else:
            err_msg = f"Process {os.getpid()} has no booster for {queue_name}, pid_queue_name__booster_map: {self.pid_queue_name__booster_map}"
            raise ValueError(err_msg)

    def get_or_create_booster_by_queue_name(
        self,
        queue_name,
    ) -> Booster:
        """
        Get booster object in current process. In multi-process mode, a new booster object is created in the new process, because some brokers don't support sharing the same connection across processes.
        :param queue_name: The parameter of @boost.
        :return:
        """

        key = gen_pid_queue_name_key(queue_name)
        if key in self.pid_queue_name__booster_map:
            return self.pid_queue_name__booster_map[key]
        else:
            with self._lock:
                if key not in self.pid_queue_name__booster_map:
                    boost_params = self.get_boost_params(queue_name)
                    booster = Booster(boost_params)(boost_params.consuming_function)
                    self.pid_queue_name__booster_map[key] = booster
                return booster

    def get_boost_params(self, queue_name: str) -> (dict, typing.Callable):
        """
        This function is for instantiating booster, consumer and publisher in other processes, getting the original parameters of the booster for the given queue_name.
        Some broker Python packages' connection objects are not multi-process safe, so don't use booster/consumer/publisher objects created in process 1 from process 2.
        """
        return self.queue_name__boost_params_map[queue_name]

    def build_booster(self, boost_params: BoosterParams) -> Booster:
        """
        Get or create a booster object in the current process. Convenient for dynamically creating boosters by queue name inside functions, without repeatedly creating consumers, publishers, and broker connections.
        :param boost_params: The parameters for @boost.
        :param consuming_function: The consuming function
        :return:
        """

        key = gen_pid_queue_name_key(boost_params.queue_name)
        if key in self.pid_queue_name__booster_map:
            booster = self.pid_queue_name__booster_map[key]
        else:
            if boost_params.consuming_function is None:
                raise ValueError(
                    f"The consuming_function field in build_booster method cannot be None, a function must be specified"
                )
            flogger.info(
                f"Creating booster {boost_params} {boost_params.consuming_function}"
            )
            booster = Booster(boost_params)(boost_params.consuming_function)
        return booster

    # queue_name__cross_project_publisher_map = {}

    def get_cross_project_publisher(
        self, publisher_params: PublisherParams
    ) -> AbstractPublisher:
        """
        Publish messages across different projects. For example, proj1 has fun1 consuming function, but proj2 cannot directly access proj1's function and cannot use fun1.push to publish.
        Use this method to get a publisher.

        publisher = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name='proj1_queue', broker_kind=publisher_params.broker_kind))
        publisher.publish({'x': aaa})
        """
        # Ensure using current registry's namespace for isolation
        if publisher_params.booster_registry_name != self.booster_registry_name:
            raise ValueError(f"publisher_params.booster_registry_name != self.booster_registry_name, {publisher_params.booster_registry_name} != {self.booster_registry_name}")
            
        return PublisherCacheProxy(publisher_params).publisher

    def push(self, queue_name, *args, **kwargs):
        """Push a message to the message queue;"""
        self.get_or_create_booster_by_queue_name(queue_name).push(*args, **kwargs)

    def publish(self, queue_name, msg):
        """Publish a message to the message queue;"""
        self.get_or_create_booster_by_queue_name(queue_name).publish(msg)

    def consume_queues(self, *queue_names):
        """
        Start consuming from multiple queue names, all function queues start consuming within the same process.
        This approach saves total memory, but cannot utilize multi-core CPUs.
        """
        for queue_name in queue_names:
            self.get_booster(queue_name).consume()
        ctrl_c_recv()

    consume = consume_queues

    def consume_all_queues(self, block=True):
        """
        Start consuming from all queue names without manually calling funxx.consume() for each function, all function queues start consuming within the same process.
        This approach saves total memory, but cannot utilize multi-core CPUs.
        """
        for queue_name in self.get_all_queues():
            self.get_booster(queue_name).consume()
        if block:
            ctrl_c_recv()

    consume_all = consume_all_queues

    def multi_process_consume_queues(self, **queue_name__process_num):
        """
        Start consuming from multiple queue names, passing queue names and process counts, each queue starts n separate consuming processes;
        This approach uses more total memory, but fully utilizes multi-core CPUs.
        E.g. multi_process_consume_queues(queue1=2,queue2=3) means start 2 processes for queue1, 3 processes for queue2.
        """
        for queue_name, process_num in queue_name__process_num.items():
            self.get_booster(queue_name).multi_process_consume(process_num)
        ctrl_c_recv()

    mp_consume = multi_process_consume_queues

    def consume_group(self, booster_group: str, block=False):
        """
        Start multiple consuming functions based on the booster_group name in the @boost decorator;
        """
        if booster_group is None:
            raise ValueError("booster_group cannot be None")
        need_consume_queue_names = []
        for queue_name in self.get_all_queues():
            booster = self.get_or_create_booster_by_queue_name(queue_name)
            if booster.boost_params.booster_group == booster_group:
                need_consume_queue_names.append(queue_name)
        flogger.info(
            f"according to booster_group:{booster_group} ,start consume queues: {need_consume_queue_names}"
        )
        for queue_name in need_consume_queue_names:
            self.get_or_create_booster_by_queue_name(queue_name).consume()
        if block:
            ctrl_c_recv()

    def multi_process_consume_group(self, booster_group: str, process_num=1):
        """
        Start multiple consuming functions based on the booster_group name in the @boost decorator using multi-process;
        """
        for _ in range(process_num):
            Process(target=self.consume_group, args=(booster_group, True)).start()

    mp_consume_group = multi_process_consume_group

    def multi_process_consume_all_queues(self, process_num=1):
        """
        Start consuming from all queue names without specifying queue names, each queue starts n separate consuming processes;
        This approach uses more total memory, but fully utilizes multi-core CPUs.
        """
        for queue_name in self.get_all_queues():
            self.get_booster(queue_name).multi_process_consume(process_num)
        ctrl_c_recv()

    mp_consume_all = multi_process_consume_all_queues


booster_registry_default = BoosterRegistry(
    booster_registry_name=StrConst.BOOSTER_REGISTRY_NAME_DEFAULT,
)
# BoostersManager is kept for backward compatibility. The original BoostersManager was a class with a set of classmethod methods.
# Now BoostersManager is an instance of BoosterRegistry, it is an object.
# With the introduction of booster_registry_name concept, it was developed as a class with instance methods for easier multi-instance isolation. The old BoostersManager only had classmethods.
BoostersManager = booster_registry_default
