# import sys
# from pathlib import Path
#
# project_root_path = str(Path(__file__).absolute().parent.parent.parent)
# print(f'project_root_path is : {project_root_path}')
# sys.path.insert(1, project_root_path)  # This is for convenience so users don't have to manually run: export PYTHONPATH=project_root_dir
#
# ##### $$$$$$$$$$$$
# #  The code above must be placed at the very top; set pythonpath before importing funboost-related modules.
# ##### $$$$$$$$$$$$
#
#
# from funboost.core.cli.funboost_fire import BoosterFire
# # Functions to be started should ideally be imported here. Otherwise specify them in --import_modules_str
# # noinspection PyUnresolvedReferences
# import def_tasks  # This imports the functions decorated with boost; important, otherwise the queue-to-function mapping is unknown
#
# # def_tasks3.py is not imported here; to operate on def_tasks3's queues, use --import_modules_str
#
# if __name__ == '__main__':
#     # ctrl_c_recv()
#
#     '''
#
#     If sys.path.insert(1, project_root_dir) is not written, first run: set PYTHONPATH=project_root_dir
#     set PYTHONPATH=/codes/funboost/
#
#
#     python test_cli.py clear test_cli1_queue   # Clear the message queue
#
#     python test_cli.py push test_cli1_queue 1 2  # Publish a message
#     python test_cli.py push test_cli1_queue 1 --y=2 # Publish a message with explicit parameter names
#     python test_cli.py publish test_cli1_queue "{'x':3,'y':4}"  # Publish a message passing a dict
#     python test_cli.py publish test_cli1_queue '{"x":3,"y":4}' # Incorrect way
#
#
#     python test_cli.py consume test_cli1_queue test_cli2_queue  # Start consuming from two queues
#     python test_cli.py mp_consume --test_cli1_queue=2 --test_cli2_queue=3 # Start multi-process consumption
#
#     # Publishing: since def_tasks3 module is not imported here, pass import_modules_str, then publish
#     # To import multiple modules, separate them with commas in import_modules_str
#     python test_cli.py --import_modules_str "test_frame.test_funboost_cli.def_tasks3"  publish test_cli3_queue "{'x':3,'y':4}"
#
#     # If the module with boost functions is not directly imported, auto-scan a directory of .py files to auto-import
#     python test_cli.py --boost_dirs_str './test_find_boosters,./test_find_boosters/d2'  push test_find_queue1 --x=1 --y=2
#
#     '''
#
#     '''
#     cd D:\codes\funboost\test_frame\test_funboost_cli && python test_cli.py consume test_cli1_queue test_cli2_queue
#     '''
