import copy
import importlib
import sys
import typing
from os import PathLike

from funboost.core.booster import BoostersManager
from funboost.core.cli.discovery_boosters import BoosterDiscovery
from funboost.utils.ctrl_c_end import ctrl_c_recv

env_dict = {'project_root_path': None}


# noinspection PyMethodMayBeStatic
class BoosterFire(object):
    def __init__(self, import_modules_str: str = None,
                 booster_dirs_str: str = None, max_depth=1, py_file_re_str: str = None, project_root_path=None):
        """
        :param project_root_path : User project root directory
        :param import_modules_str:
        :param booster_dirs_str: Directory to scan for @boost functions; separate multiple directories with commas
        :param max_depth: Depth of directory scanning
        :param py_file_re_str: Regex for Python files, e.g. tasks.py so that only files matching this pattern are auto-imported
        """
        project_root_path = env_dict['project_root_path'] or project_root_path
        print(f'project_root_path is :{project_root_path} , please verify')
        if project_root_path is None:
            raise Exception('project_root_path is none')
        loc = copy.copy(locals())
        for k, v in loc.items():
            print(f'{k} : {v}')
        sys.path.insert(1, str(project_root_path))
        self.import_modules_str = import_modules_str
        if import_modules_str:
            for m in self.import_modules_str.split(','):
                importlib.import_module(m)  # Discover @boost functions
        if booster_dirs_str and project_root_path:
            boost_dirs = booster_dirs_str.split(',')
            BoosterDiscovery(project_root_path=str(project_root_path), booster_dirs=boost_dirs,
                             max_depth=max_depth, py_file_re_str=py_file_re_str).auto_discovery()  # Discover @boost functions

    def show_all_queues(self):
        """Display all discovered queue names."""
        print(f'get_all_queues: {BoostersManager.get_all_queues()}')
        return self

    def clear(self, *queue_names: str):
        """
        Clear multiple queues; example: clear test_cli1_queue1  test_cli1_queue2   # Clear 2 message queues
        """

        for queue_name in queue_names:
            BoostersManager.get_booster(queue_name).clear()
        return self

    def push(self, queue_name, *args, **kwargs):
        """Push a message to the message queue;
        Example: assuming the function is def add(x,y) and the queue name is add_queue, to publish 1 + 2:
        push add_queue 1 2;
        or push add_queue --x=1 --y=2;
        or push add_queue -x 1 -y 2;
        """
        BoostersManager.push(queue_name,*args, **kwargs)
        return self

    def __str__(self):
        # print('over')  # This line is important; without it, chained CLI calls cannot exit automatically
        return ''

    def publish(self, queue_name, msg):
        """Publish a message to the message queue;
           Assuming the function is def add(x,y) and the queue name is add_queue, to publish 1 + 2:
           publish add_queue "{'x':1,'y':2}"
        """

        BoostersManager.publish(queue_name,msg)
        return self

    def consume_queues(self, *queue_names: str):
        """
        Start consuming from multiple queue names;
        Example: consume queue1 queue2
        """
        BoostersManager.consume_queues(*queue_names)

    consume = consume_queues

    def consume_all_queues(self, ):
        """
        Start consuming from all queue names, no need to specify queue names;
        Example: consume_all_queues
        """
        BoostersManager.consume_all_queues()

    consume_all = consume_all_queues

    def multi_process_consume_queues(self, **queue_name__process_num):
        """
        Start consuming using multiple processes, each queue launches multiple separate consuming processes;
        Example: mp_consume --queue1=2 --queue2=3    # queue1 starts 2 separate processes, queue2 starts 3
        """
        BoostersManager.multi_process_consume_queues(**queue_name__process_num)

    mp_consume = multi_process_consume_queues

    def multi_process_consume_all_queues(self, process_num=1):
        """
        Start consuming from all queue names without specifying them, each queue launches n separate consuming processes;
        Example: multi_process_consume_all_queues 2
        """
        BoostersManager.multi_process_consume_all_queues(process_num)

    mp_consume_all = multi_process_consume_all_queues

    def pause(self, *queue_names: str):
        """
        Pause consuming from multiple queue names;
        Example: pause queue1 queue2
        """
        for queue_name in queue_names:
            BoostersManager.get_booster(queue_name).pause()

    def continue_consume(self, *queue_names: str):
        """
        Resume consuming from multiple queue names;
        Example: continue_consume queue1 queue2
        """
        for queue_name in queue_names:
            BoostersManager.get_booster(queue_name).continue_consume()
    
    def start_funboost_web_manager(self):
        """
        Start the funboost web manager;
        Example: start_funboost_web_manager
        """
        from funboost.funweb.app import start_funboost_web_manager
        start_funboost_web_manager()

    start_web = start_funboost_web_manager
