"""
funboost now supports launching consumption, publishing, and clearing messages from the command line.


"""
import sys
from pathlib import Path
import fire

project_root_path = Path(__file__).absolute().parent
print(f'project_root_path is : {project_root_path}  , please verify this is correct')
sys.path.insert(1, str(project_root_path))  # this allows command-line users to avoid manually running: export PYTHONPATH=<project-root>

# $$$$$$$$$$$$
# The sys.path code above must be placed at the very top so that the Python path is set before any funboost-related modules are imported.
# $$$$$$$$$$$$


from funboost.core.cli.funboost_fire import BoosterFire, env_dict
from funboost.core.cli.discovery_boosters import BoosterDiscovery

# Functions that need to be started should ideally be imported into this module; otherwise, specify which modules in the user project contain boosters via --import_modules_str or booster_dirs.
'''
There are 4 ways to automatically locate modules decorated with @boost and register boosters:

1. The user manually imports the module or function containing the consumer function to start into this module.
2. The user specifies --import_modules_str on the command line to indicate which module paths to import, enabling consumption and publishing for those queue names.
3. The user calls BoosterDiscovery.auto_discovery_boosters to automatically import all .py files under a specified directory.
4. The user passes project_root_path and booster_dirs on the command line to automatically scan and import modules.
'''
env_dict['project_root_path'] = project_root_path

if __name__ == '__main__':
    # booster_dirs: users can add extra directories to scan here, reducing the need to pass --booster_dirs_str on the command line.
    # BoosterDiscovery can be called multiple times.
    BoosterDiscovery(project_root_path, booster_dirs=[], max_depth=1, py_file_re_str=None).auto_discovery()  # best placed inside main; if scanning its own directory without a regex to exclude itself, it will cause an infinite import loop.
    fire.Fire(BoosterFire, )

'''

python /codes/funboost/funboost_cli_user.py   --booster_dirs_str=test_frame/test_funboost_cli/test_find_boosters --max_depth=2  push test_find_queue1 --x=1 --y=2

python /codes/funboost/funboost_cli_user.py   --booster_dirs_str=test_frame/test_funboost_cli/test_find_boosters --max_depth=2  consume test_find_queue1 

'''
