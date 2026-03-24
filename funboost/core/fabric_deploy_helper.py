# noinspection PyDefaultArgument
import sys
import threading
import time
from pathlib import Path
from fabric2 import Connection
from nb_libs.path_helper import PathHelper
from funboost.utils.paramiko_util import ParamikoFolderUploader

from funboost.core.loggers import get_funboost_file_logger
from funboost.core.booster import Booster

logger = get_funboost_file_logger(__name__)


# noinspection PyDefaultArgument
def fabric_deploy(booster: Booster, host, port, user, password,
                  path_pattern_exluded_tuple=('/.git/', '/.idea/', '/dist/', '/build/'),
                  file_suffix_tuple_exluded=('.pyc', '.log', '.gz'),
                  only_upload_within_the_last_modify_time=3650 * 24 * 60 * 60,
                  file_volume_limit=1000 * 1000, sftp_log_level=20, extra_shell_str='',
                  invoke_runner_kwargs={'hide': None, 'pty': True, 'warn': False},
                  python_interpreter='python3',
                  process_num=1,
                  pkey_file_path=None,
                  ):
    “””
    No dependency on Alibaba Cloud CodePipeline or any DevOps deployment tools, multi-machine remote deployment can be achieved purely at the Python code level.
    This implements function-level precise deployment, not just deploying a .py file. Remote deployment of a function is more challenging than a script, but more flexible.

    Previously people asked how to conveniently deploy on multiple machines, typically using Alibaba Cloud CodePipeline or K8s auto-deployment. The remote machines must be Linux, not Windows.
    For those who directly manage multiple physical machines, it can be inconvenient. Now there's a cross-machine auto-deployment using Python code itself to run function tasks.

    Automatically converts the task function's file location into a Python module path, achieving function-level precise deployment, more precise than script-level deployment.
    E.g. test_frame/test_fabric_deploy/test_deploy1.py's fun2 function is automatically converted to: from test_frame.test_fabric_deploy.test_deploy1 import f2
    Thus auto-generating the deployment statement:
    export PYTHONPATH=/home/ydf/codes/distributed_framework:$PYTHONPATH ;cd /home/ydf/codes/distributed_framework;
    python3 -c “from test_frame.test_fabric_deploy.test_deploy1 import f2;f2.multi_process_consume(2)”  -funboostmark funboost_fabric_mark_queue_test30

    This can directly run function tasks on remote machines. No need for users to manually deploy code or start code. Auto-uploads code, auto-sets environment variables, auto-imports functions, auto-runs.
    The principle uses python -c for function-level deployment, not script-level deployment.
    You can flexibly specify which machine runs which function with how many processes. This is more powerful than Celery, which requires logging into each machine, manually downloading code and deploying on multiple machines. Celery doesn't support auto-running code on other machines.


    :param booster: Function decorated with @boost
    :param host: IP of the remote Linux machine to deploy to
    :param port: Port of the remote Linux machine to deploy to
    :param user: Username of the remote Linux machine
    :param password: Password of the remote Linux machine
    :param path_pattern_exluded_tuple: Excluded folder or file path patterns
    :param file_suffix_tuple_exluded: Excluded file suffixes
    :param only_upload_within_the_last_modify_time: Only upload files modified within this many seconds. After a full upload, reduce this value to avoid full uploads each time.
    :param file_volume_limit: Files larger than this size won't be uploaded, since Python code files rarely exceed 1M
    :param sftp_log_level: File upload log level. 10=logging.DEBUG, 20=logging.INFO, 30=logging.WARNING
    :param extra_shell_str: Extra commands to execute before auto-deployment, e.g. setting environment variables
    :param python_interpreter: Python interpreter path. If multiple Python environments are installed on Linux, specify the absolute path.
    :param invoke_runner_kwargs: All parameters for the invoke package's runner.py run() method. The example shows a few parameters, but you can pass dozens. Explore fabric's run method and pass as needed.
                                 hide: whether to hide remote machine output. False=show all, “out”=hide stdout only, “err”=hide stderr only, True=hide all output.
                                 pty: whether the remote deployment process ends when the current script ends. True=remote process ends with local script. False=remote machine continues running even after local script closes.
                                 warn: whether local code exits immediately if remote machine returns an error code. True=just warn, False=terminate local code on remote error code.
    :param process_num: Number of processes to start. For maximum CPU performance, set to the number of CPU cores. Each process has its own concurrency mode and count specified by the task function, so it's multi-process + threads/coroutines.
    :param pkey_file_path: Private key file path. If set, uses SSH private key to login to remote machine; otherwise uses password.
    :return:


    task_fun.fabric_deploy('192.168.6.133', 22, 'ydf', '123456', process_num=2) is all you need to auto-deploy and run on a remote machine.
    “””
    # print(locals())
    python_proj_dir = Path(sys.path[1]).resolve().as_posix() + '/'
    python_proj_dir_short = python_proj_dir.split('/')[-2]
    # Get the module filename where the called function is located
    file_name = Path(sys._getframe(2).f_code.co_filename).resolve().as_posix() # noqa
    relative_file_name = Path(file_name).relative_to(Path(python_proj_dir)).as_posix()
    relative_module = relative_file_name.replace('/', '.')[:-3]  # -3 to remove .py
    func_name = booster.consuming_function.__name__

    """The following is for compatibility with functions without @boost that use boosterxx = BoostersManager.build_booster() to create boosters. func_name is needed in python_exec_str below.
    You can also use BoostersManager.get_booster(queue_name) remotely and then start consuming. Since importing the module registers booster info to BoostersManager, it can then be started.
    """
    module_obj = PathHelper(sys._getframe(2).f_code.co_filename).import_as_module()  # noqa
    for var_name,var_value in module_obj.__dict__.items():
        if isinstance(var_value,Booster) and var_value.queue_name == booster.queue_name:
            func_name = var_name

    logger.debug([file_name, python_proj_dir, python_proj_dir_short,relative_module, func_name])
    # print(relative_module)
    if user == 'root':  # Folders will be auto-created, no need for users to create them.
        remote_dir = f'/codes/{python_proj_dir_short}'
    else:
        remote_dir = f'/home/{user}/codes/{python_proj_dir_short}'

    def _inner():
        logger.warning(f'Uploading local code folder {python_proj_dir} to remote {host} folder {remote_dir}.')
        t_start = time.perf_counter()
        uploader = ParamikoFolderUploader(host, port, user, password, python_proj_dir, remote_dir,
                                          path_pattern_exluded_tuple, file_suffix_tuple_exluded,
                                          only_upload_within_the_last_modify_time, file_volume_limit, sftp_log_level, pkey_file_path)
        uploader.upload()
        logger.info(f'Uploading local code folder {python_proj_dir} to remote {host} folder {remote_dir} took {round(time.perf_counter() - t_start, 3)} seconds')
        # conn.run(f'''export PYTHONPATH={remote_dir}:$PYTHONPATH''')

        queue_name = booster.consumer.queue_name
        process_mark = f'funboost_fabric_mark__{queue_name}__{func_name}'
        conn = Connection(host, port=port, user=user, connect_kwargs={"password": password}, )
        kill_shell = f'''ps -aux|grep {process_mark}|grep -v grep|awk '{{print $2}}' |xargs kill -9'''
        logger.warning(f'Using linux command {kill_shell} to kill processes with mark {process_mark}')
        # uploader.ssh.exec_command(kill_shell)
        conn.run(kill_shell, encoding='utf-8', warn=True)  # Don't want to prompt, to avoid disturbing users into thinking something is wrong. Using paramiko's ssh.exec_command above

        python_exec_str = f'''export is_funboost_remote_run=1;export PYTHONPATH={remote_dir}:$PYTHONPATH ;{python_interpreter} -c "from {relative_module} import {func_name};{func_name}.multi_process_consume({process_num})"  -funboostmark {process_mark} '''
        shell_str = f'''cd {remote_dir}; {python_exec_str}'''
        extra_shell_str2 = extra_shell_str  # Inner function cannot directly modify outer variable.
        if not extra_shell_str2.endswith(';') and extra_shell_str != '':
            extra_shell_str2 += ';'
        shell_str = extra_shell_str2 + shell_str
        logger.warning(f'Using linux command {shell_str} to start task consuming on remote machine {host}')
        conn.run(shell_str, encoding='utf-8', **invoke_runner_kwargs)
        # uploader.ssh.exec_command(shell_str)

    threading.Thread(target=_inner).start()


def kill_all_remote_tasks(host, port, user, password):
    """Use with caution, this kills all remotely deployed tasks, generally not needed"""
    uploader = ParamikoFolderUploader(host, port, user, password, '', '')
    funboost_fabric_mark_all = 'funboost_fabric_mark__'
    kill_shell = f'''ps -aux|grep {funboost_fabric_mark_all}|grep -v grep|awk '{{print $2}}' |xargs kill -9'''
    logger.warning(f'Using linux command {kill_shell} to kill processes with mark {funboost_fabric_mark_all}')
    uploader.ssh.exec_command(kill_shell)
    logger.warning(f'Killed all processes with mark {funboost_fabric_mark_all} on machine {host}')
