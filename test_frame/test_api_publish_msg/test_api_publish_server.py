from pathlib import Path

from funboost.contrib.api_publish_msg import app, BoosterDiscovery

'''
# If the user does not use BoosterDiscovery, they need to import the modules containing boost-related functions,
# otherwise the queue-related function definitions cannot be found by queue name.
Need to:
import test_frame.test_api_publish_msg.tasks.boost1
import test_frame.test_api_publish_msg.tasks.boost2
'''
BoosterDiscovery(project_root_path=Path(__file__).absolute().parent.parent.parent,
                 booster_dirs=[Path(__file__).absolute().parent / Path('tasks')]).auto_discovery()

if __name__ == '__main__':
    '''
    uvicorn test_frame.test_api_publish_msg.test_api_publish_server:app --workers 4 --port 16667
    '''
    import uvicorn

    uvicorn.run('funboost.contrib.api_publish_msg:app', host="0.0.0.0", port=16667, workers=4)
