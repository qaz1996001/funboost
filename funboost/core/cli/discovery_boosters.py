"""
[⚠️ Security Warning & Best Practices]

1. Risk Warning for BoosterDiscovery Auto-Scanning
-------------------------------------------------------
BoosterDiscovery(....).auto_discovery() must be used with great care. It is strongly recommended to pass precise filter parameters when instantiating.

Reason:
    Some developers may have loose coding habits: scripts that perform actions at module level may lack
    `if __name__ == '__main__':` protection, or the author may not understand how `__main__` works.
    Python's import mechanism means "importing a module executes its top-level code."

Dangerous scenario:
    Suppose there is a temporary dirty-data cleanup script `my_temp_dangerous_delete_mysql_script.py` in the project:

    ```python
    # ❌ Dangerous: written at module top level, not inside a function, and without main guard
    import db_client
    db_client.execute("DROP TABLE users")
    ```

Consequence:
    If you use unrestricted `auto_discovery()`, even 2 years after the project goes live, once this script
    is scanned and imported, the database table will be deleted instantly. This is an absolute production disaster.

✅ Correct usage (with precise parameters):
    BoosterDiscovery(
        project_root_path='/path/to/your_project',
        booster_dirs=['your_booster_dir'],
        max_depth=1,
        py_file_re_str='tasks'  # Strongly recommended: only scan files containing 'tasks', avoiding temp scripts
    ).auto_discovery()


2. Why prefer "explicit Import" over "auto-scanning"? BoosterDiscovery is NOT required by funboost!
-------------------------------------------------------
It is actually not recommended to over-rely on `auto_discovery()`. The recommended best practice is:
👉 Manually and explicitly import the modules containing @boost. Import only what you need.

Architecture difference between Funboost and Celery:
    * Funboost:
      Has no central `app` instance, no need for a separate `celery_app.py` module like Celery.
      Architecturally, there is no "circular import deadlock" by design. Just import the consuming functions you need — simple and straightforward.

    * Celery:
      Must manually configure `includes` or call `autodiscover_tasks()`.
      The root cause: Celery's `xx_tasks.py` needs to import the `app` object from `celery_app.py`;
      while `celery worker` starting `app` also needs to import `xx_tasks.py` to register tasks.
      This design traps both sides in a circular import deadlock, forcing Celery to invent a complex import mechanism
      and making newcomers very careful and frustrated when planning the project directory structure.
""" 

import re
import sys
import typing
from os import PathLike
from pathlib import Path
import importlib.util
# import nb_log
from funboost.core.loggers import FunboostFileLoggerMixin
from funboost.utils.decorators import flyweight
from funboost.core.lazy_impoter import funboost_lazy_impoter

# @flyweight
class BoosterDiscovery(FunboostFileLoggerMixin):
    def __init__(self, project_root_path: typing.Union[PathLike, str],
                 booster_dirs: typing.List[typing.Union[PathLike, str]],
                 max_depth=1, py_file_re_str: str = None):
        """
        :param project_root_path: Project root directory
        :param booster_dirs: Folder(s) containing modules with @boost decorator functions, no need to include the full project root path
        :param max_depth: How many levels of subdirectories to search
        :param py_file_re_str: Filename match filter. E.g. if all your consuming functions are in xxx_task.py, yyy_task.py etc., you can pass 'task.py' to avoid auto-importing unneeded modules.

        BoosterDiscovery(....).auto_discovery() must be used with caution and precise parameters. See the module-level comment above for reasons.

        """
        self.project_root_path = project_root_path
        self.booster__full_path_dirs = [Path(project_root_path) / Path(boost_dir) for boost_dir in booster_dirs]
        self.max_depth = max_depth
        self.py_file_re_str = py_file_re_str

        self.py_files = []
        self._has_discovery_import = False

    def get_py_files_recursively(self, current_folder_path: Path, current_depth=0, ):
        """First find all py files."""
        if current_depth > self.max_depth:
            return
        for item in current_folder_path.iterdir():
            if item.is_dir():
                self.get_py_files_recursively(item, current_depth + 1)
            elif item.suffix == '.py':
                if self.py_file_re_str:
                    if re.search(self.py_file_re_str, str(item), ):
                        self.py_files.append(str(item))
                else:
                    self.py_files.append(str(item))
        self.py_files = list(set(self.py_files))

    def auto_discovery(self, ):
        """Automatically import all py files, mainly to register all @boost function decorators into pid_queue_name__booster_map.
        This auto_discovery method is best placed inside main; if scanning the folder containing this file itself without a regex to exclude it, it will cause infinite circular imports.
        """
        if self._has_discovery_import is False:
            self._has_discovery_import = True
        else:
            pass
            return  # This check prevents infinite circular imports if the user calls BoosterDiscovery.auto_discovery() outside of `if __name__ == '__main__'`.
        self.logger.info(self.booster__full_path_dirs)
        for dir in self.booster__full_path_dirs:
            if not Path(dir).exists():
                raise Exception(f'This folder does not exist ->  {dir}')

            self.get_py_files_recursively(Path(dir))
            for file_path in self.py_files:
                self.logger.debug(f'Importing module {file_path}')
                if Path(file_path) == Path(sys._getframe(1).f_code.co_filename):
                    self.logger.warning(f'Excluding auto_discovery caller module itself from import: {file_path}')  # Otherwise importing this file would cause infinite circular imports.
                    continue

                # module_name = Path(file_path).as_posix().replace('/', '.') + '.' + Path(file_path).stem
                module_name = Path(file_path).relative_to(Path(self.project_root_path)).with_suffix('').as_posix().replace('/', '.').replace('\\', '.')
                # print(module_name, file_path)
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
        funboost_lazy_impoter.BoostersManager.show_all_boosters()


if __name__ == '__main__':
    # Specify the folder path
    BoosterDiscovery(project_root_path='/codes/funboost',
                     booster_dirs=['test_frame/test_funboost_cli/test_find_boosters'],
                     max_depth=2, py_file_re_str='task').auto_discovery()
