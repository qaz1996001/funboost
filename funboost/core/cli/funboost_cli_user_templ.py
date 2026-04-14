"""
funboost now supports command-line launching of consumers, publishers, and clearing messages.


"""
import sys
from pathlib import Path
import fire

project_root_path = Path(__file__).absolute().parent
print(f'project_root_path is : {project_root_path}  , please verify this is correct')
sys.path.insert(1, str(project_root_path))  # This makes it convenient to use the CLI without manually running 'export PYTHONPATH=project_root_dir' first.

# $$$$$$$$$$$$
# The sys.path code above must be placed at the top, setting up PYTHONPATH before importing funboost-related modules.
# $$$$$$$$$$$$


from funboost.core.cli.funboost_fire import BoosterFire, env_dict
from funboost.core.cli.discovery_boosters import BoosterDiscovery

# For functions to be started, it is recommended to import the module or function here,
# otherwise specify the modules containing boosters via --import_modules_str or booster_dirs.
'''
There are 4 ways to auto-discover @boost decorators and register boosters:

1. Manually import the module or function containing the consuming function into this module.
2. Use --import_modules_str on the command line to specify which module paths to import, enabling consumption and publishing for those queue names.
3. Use BoosterDiscovery.auto_discovery_boosters to automatically import .py files in a specified folder.
4. Pass project_root_path and booster_dirs on the command line to auto-scan and import modules.
'''
env_dict['project_root_path'] = project_root_path

if __name__ == '__main__':
    # booster_dirs: users can add additional folders to scan, reducing the need to pass --booster_dirs_str on the CLI.
    # BoosterDiscovery can be called multiple times.
    BoosterDiscovery(project_root_path, booster_dirs=[], max_depth=1, py_file_re_str=None).auto_discovery()  # Best placed inside main; if scanning its own folder without a regex to exclude the file itself, it will cause infinite circular imports.
    fire.Fire(BoosterFire, )

'''

python /codes/funboost/funboost_cli_user.py   --booster_dirs_str=test_frame/test_funboost_cli/test_find_boosters --max_depth=2  push test_find_queue1 --x=1 --y=2

python /codes/funboost/funboost_cli_user.py   --booster_dirs_str=test_frame/test_funboost_cli/test_find_boosters --max_depth=2  consume test_find_queue1 

'''
