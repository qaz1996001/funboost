# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/4/11 0011 0:56
"""

Use an override approach for configuration.
"""
import sys
import time
import importlib
import json
from pathlib import Path
from shutil import copyfile

from funboost.core.funboost_config_getter import _try_get_user_funboost_common_config
from funboost.core.loggers import flogger, get_funboost_file_logger, logger_prompt
from nb_log import nb_print, stderr_write, stdout_write
from nb_log.monkey_print import is_main_process, only_print_on_main_process
from funboost import funboost_config_deafult


def show_funboost_flag():
    funboost_flag_str = '''


    FFFFFFFFFFFFFFFFFFFFFF     UUUUUUUU     UUUUUUUU     NNNNNNNN        NNNNNNNN     BBBBBBBBBBBBBBBBB             OOOOOOOOO               OOOOOOOOO             SSSSSSSSSSSSSSS      TTTTTTTTTTTTTTTTTTTTTTT
    F::::::::::::::::::::F     U::::::U     U::::::U     N:::::::N       N::::::N     B::::::::::::::::B          OO:::::::::OO           OO:::::::::OO         SS:::::::::::::::S     T:::::::::::::::::::::T
    F::::::::::::::::::::F     U::::::U     U::::::U     N::::::::N      N::::::N     B::::::BBBBBB:::::B       OO:::::::::::::OO       OO:::::::::::::OO      S:::::SSSSSS::::::S     T:::::::::::::::::::::T
    FF::::::FFFFFFFFF::::F     UU:::::U     U:::::UU     N:::::::::N     N::::::N     BB:::::B     B:::::B     O:::::::OOO:::::::O     O:::::::OOO:::::::O     S:::::S     SSSSSSS     T:::::TT:::::::TT:::::T
      F:::::F       FFFFFF      U:::::U     U:::::U      N::::::::::N    N::::::N       B::::B     B:::::B     O::::::O   O::::::O     O::::::O   O::::::O     S:::::S                 TTTTTT  T:::::T  TTTTTT
      F:::::F                   U:::::D     D:::::U      N:::::::::::N   N::::::N       B::::B     B:::::B     O:::::O     O:::::O     O:::::O     O:::::O     S:::::S                         T:::::T        
      F::::::FFFFFFFFFF         U:::::D     D:::::U      N:::::::N::::N  N::::::N       B::::BBBBBB:::::B      O:::::O     O:::::O     O:::::O     O:::::O      S::::SSSS                      T:::::T        
      F:::::::::::::::F         U:::::D     D:::::U      N::::::N N::::N N::::::N       B:::::::::::::BB       O:::::O     O:::::O     O:::::O     O:::::O       SS::::::SSSSS                 T:::::T        
      F:::::::::::::::F         U:::::D     D:::::U      N::::::N  N::::N:::::::N       B::::BBBBBB:::::B      O:::::O     O:::::O     O:::::O     O:::::O         SSS::::::::SS               T:::::T        
      F::::::FFFFFFFFFF         U:::::D     D:::::U      N::::::N   N:::::::::::N       B::::B     B:::::B     O:::::O     O:::::O     O:::::O     O:::::O            SSSSSS::::S              T:::::T        
      F:::::F                   U:::::D     D:::::U      N::::::N    N::::::::::N       B::::B     B:::::B     O:::::O     O:::::O     O:::::O     O:::::O                 S:::::S             T:::::T        
      F:::::F                   U::::::U   U::::::U      N::::::N     N:::::::::N       B::::B     B:::::B     O::::::O   O::::::O     O::::::O   O::::::O                 S:::::S             T:::::T        
    FF:::::::FF                 U:::::::UUU:::::::U      N::::::N      N::::::::N     BB:::::BBBBBB::::::B     O:::::::OOO:::::::O     O:::::::OOO:::::::O     SSSSSSS     S:::::S           TT:::::::TT      
    F::::::::FF                  UU:::::::::::::UU       N::::::N       N:::::::N     B:::::::::::::::::B       OO:::::::::::::OO       OO:::::::::::::OO      S::::::SSSSSS:::::S           T:::::::::T      
    F::::::::FF                    UU:::::::::UU         N::::::N        N::::::N     B::::::::::::::::B          OO:::::::::OO           OO:::::::::OO        S:::::::::::::::SS            T:::::::::T      
    FFFFFFFFFFF                      UUUUUUUUU           NNNNNNNN         NNNNNNN     BBBBBBBBBBBBBBBBB             OOOOOOOOO               OOOOOOOOO           SSSSSSSSSSSSSSS              TTTTTTTTTTT      


    '''

    funboost_flag_str2 = r'''

          ___                  ___                    ___                                           ___                    ___                    ___                          
         /  /\                /__/\                  /__/\                  _____                  /  /\                  /  /\                  /  /\                   ___   
        /  /:/_               \  \:\                 \  \:\                /  /::\                /  /::\                /  /::\                /  /:/_                 /  /\  
       /  /:/ /\               \  \:\                 \  \:\              /  /:/\:\              /  /:/\:\              /  /:/\:\              /  /:/ /\               /  /:/  
      /  /:/ /:/           ___  \  \:\            _____\__\:\            /  /:/~/::\            /  /:/  \:\            /  /:/  \:\            /  /:/ /::\             /  /:/   
     /__/:/ /:/           /__/\  \__\:\          /__/::::::::\          /__/:/ /:/\:|          /__/:/ \__\:\          /__/:/ \__\:\          /__/:/ /:/\:\           /  /::\   
     \  \:\/:/            \  \:\ /  /:/          \  \:\~~\~~\/          \  \:\/:/~/:/          \  \:\ /  /:/          \  \:\ /  /:/          \  \:\/:/~/:/          /__/:/\:\  
      \  \::/              \  \:\  /:/            \  \:\  ~~~            \  \::/ /:/            \  \:\  /:/            \  \:\  /:/            \  \::/ /:/           \__\/  \:\ 
       \  \:\               \  \:\/:/              \  \:\                 \  \:\/:/              \  \:\/:/              \  \:\/:/              \__\/ /:/                 \  \:\
        \  \:\               \  \::/                \  \:\                 \  \::/                \  \::/                \  \::/                 /__/:/                   \__\/
         \__\/                \__\/                  \__\/                  \__\/                  \__\/                  \__\/                  \__\/                         



    '''

    logger_prompt.debug('\033[0m' + funboost_flag_str2 + '\033[0m')

    logger_prompt.debug(f'''Distributed function scheduling framework funboost documentation:  \033[0m https://funboost.readthedocs.io/zh-cn/latest/ \033[0m ''')


show_funboost_flag()


def dict2json(dictx: dict, indent=4):
    dict_new = {}
    for k, v in dictx.items():
        # only_print_on_main_process(f'{k} :  {v}')
        if isinstance(v, (bool, tuple, dict, float, int)):
            dict_new[k] = v
        else:
            dict_new[k] = str(v)
    return json.dumps(dict_new, ensure_ascii=False, indent=indent)


def show_frame_config():
    if is_main_process():
        logger_prompt.debug('Displaying current project middleware configuration parameters')
        # for var_name in dir(funboost_config_deafult):
        #     if var_name.isupper():
        #         var_value = getattr(funboost_config_deafult, var_name)
        #         if var_name == 'MONGO_CONNECT_URL':
        #             if re.match('mongodb://.*?:.*?@.*?/.*', var_value):
        #                 mongo_pass = re.search('mongodb://.*?:(.*?)@', var_value).group(1)
        #                 mongo_pass_encryption = f'{"*" * (len(mongo_pass) - 2)}{mongo_pass[-1]}' if len(
        #                     mongo_pass) > 3 else mongo_pass
        #                 var_value_encryption = re.sub(r':(\w+)@', f':{mongo_pass_encryption}@', var_value)
        #                 only_print_on_main_process(f'{var_name}:             {var_value_encryption}')
        #                 continue
        #         if 'PASS' in var_name and var_value is not None and len(var_value) > 3:  # mask the password with asterisks
        #             only_print_on_main_process(f'{var_name}:                {var_value[0]}{"*" * (len(var_value) - 2)}{var_value[-1]}')
        #         else:
        #             only_print_on_main_process(f'{var_name}:                {var_value}')
        logger_prompt.debug(f'''The BrokerConnConfig configuration read is:\n {funboost_config_deafult.BrokerConnConfig().get_pwd_enc_json(indent=4)} ''')

        logger_prompt.debug(f'''The FunboostCommonConfig configuration read is:\n  {funboost_config_deafult.FunboostCommonConfig().get_json(indent=4)} ''')

    # only_print_on_main_process(f'The default global configuration of the BoostDecoratorDefaultParams @boost decorator input parameters is: \n  '
    #                            f'{funboost_config_deafult.BoostDecoratorDefaultParams().get_json()}')


def use_config_form_funboost_config_module():
    """
    Automatically reads configuration. It will preferentially read the funboost_config.py file in the directory of the startup script. If not found, it reads the funboost_config.py in the project root directory.
    :return:
    """
    current_script_path = sys.path[0].replace('\\', '/')
    project_root_path = sys.path[1].replace('\\', '/')
    inspect_msg = f"""
    The distributed function scheduling framework will automatically import the funboost_config module.
    When the script is run for the first time, the framework will create a file named funboost_config.py in the root directory {project_root_path} of your current Python project.
    Configuration is read automatically, preferring the funboost_config.py file in the startup script's directory {current_script_path}.
    If there is no {current_script_path}/funboost_config.py file, it will read the funboost_config.py in the project root directory {project_root_path} for configuration.
    As long as funboost_config.py is in any folder on the PYTHONPATH, it will be automatically detected.
    In the file "{project_root_path}/funboost_config.py:1", you need to set the keys and values for the middleware you intend to use. For example, if you use Redis instead of RabbitMQ as the middleware, you do not need to configure RabbitMQ.
    """
    # sys.stdout.write(f'\033[0;33m{time.strftime("%H:%M:%S")}\033[0m  "{__file__}:{sys._getframe().f_lineno}"   \033[0;30;43m{inspect_msg}\033[0m\n')
    # noinspection PyProtectedMember
    if is_main_process() and _try_get_user_funboost_common_config('SHOW_HOW_FUNBOOST_CONFIG_SETTINGS') in (True, None):
        logger_prompt.debug(f'\033[0;93m{time.strftime("%H:%M:%S")}\033[0m  "{__file__}:{sys._getframe().f_lineno}"   \033[0;93;100m{inspect_msg}\033[0m\n')
    try:
        # noinspection PyUnresolvedReferences
        # import funboost_config
        m = importlib.import_module('funboost_config')
        importlib.reload(m)  # This line prevents the case where the user wrote something like `from funboost_config import REDIS_HOST` before importing the framework, which would cause m.__dict__.items() to not include all configuration variables.
        # print(dir(m))
        # nb_print(m.__dict__.items())
        if is_main_process():
            logger_prompt.debug(f'The distributed function scheduling framework has read the variables in\n "{m.__file__}:1" as the priority configuration.\n')
        if not hasattr(m, 'BrokerConnConfig'):
            raise EnvironmentError(f'funboost version 30.0 upgraded the configuration file; middleware configuration is now written as a class. Please delete the old funboost_config.py configuration file:\n "{m.__file__}:1"')
        funboost_config_deafult.BrokerConnConfig.update_cls_attribute(**m.BrokerConnConfig().get_dict())
        funboost_config_deafult.FunboostCommonConfig.update_cls_attribute(**m.FunboostCommonConfig().get_dict())
        # funboost_config_deafult.BoostDecoratorDefaultParams.update_cls_attribute(**m.BoostDecoratorDefaultParams().get_dict())
        if hasattr(m, 'BoostDecoratorDefaultParams'):
            raise ValueError('After funboost version 40.0, BoostParams class or subclass (pydantic model) is used for input parameters; the BoostDecoratorDefaultParams configuration in funboost_config.py is no longer supported. Please remove the BoostDecoratorDefaultParams configuration.')


    except ModuleNotFoundError:
        nb_print(
            f'''The distributed function scheduling framework detected that there is no funboost_config.py file in your project root directory {project_root_path} or current folder {current_script_path}.\n''')
        _auto_creat_config_file_to_project_root_path()
    else:
        show_frame_config()
        # print(getattr(m,'BoostDecoratorDefaultParams')().get_dict())


def _auto_creat_config_file_to_project_root_path():
    """
    When not running code via PyCharm (i.e., running via cmd or Linux shell with `python xx.py`),
    please set the PYTHONPATH in a temporary session window: on Linux use `export PYTHONPATH=your_project_root`, on Windows use `set PYTHONPATH=your_project_root`.
    :return:
    """
    # print(Path(sys.path[1]).as_posix())
    # print((Path(__file__).parent.parent).absolute().as_posix())
    # if Path(sys.path[1]).as_posix() in Path(__file__).parent.parent.absolute().as_posix():
    #     nb_print('Do not want to create inside this project')
    #     return
    if '/lib/python' in sys.path[1] or r'\lib\python' in sys.path[1] or '.zip' in sys.path[1]:
        raise EnvironmentError(f'''If you are starting the script via cmd or shell rather than an IDE like PyCharm, please first set a temporary PYTHONPATH in the session window to your project path.
                               Windows cmd: use `set PYTHONPATH=your_current_python_project_root`,
                               Windows PowerShell: use `$env:PYTHONPATH=your_current_python_project_root`,
                               Linux: use `export PYTHONPATH=your_current_python_project_root`.
                               The role of PYTHONPATH is basic Python knowledge; please search online if unfamiliar.
                               You need to set a temporary environment variable in the session window command line, not by modifying Linux config files to set a permanent environment variable. Each Python project's PYTHONPATH should be different; do not hard-code it in config files.

                               To understand the importance and utility of PYTHONPATH, see: https://github.com/ydf0509/pythonpathdemo
                               ''')
        return  # When PYTHONPATH is not set, do not create a config file in places like /lib/python36.zip.

    file_name = Path(sys.path[1]) / Path('funboost_config.py')
    copyfile(Path(__file__).absolute().parent / Path('funboost_config_deafult.py'), file_name)
    nb_print(f'A file has been automatically generated in the {Path(sys.path[1])} directory. Please refresh the folder to view or modify \n "{file_name}:1"')
    # with (file_name).open(mode='w', encoding='utf8') as f:
    #     nb_print(f'A file has been automatically generated in the {file_name} directory. Please view or modify \n "{file_name}:1"')
    #     f.write(config_file_content)

    file_name = Path(sys.path[1]) / Path('funboost_cli_user.py')
    copyfile(Path(__file__).absolute().parent / Path('core/cli/funboost_cli_user_templ.py'), file_name)


use_config_form_funboost_config_module()
