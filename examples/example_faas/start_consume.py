"""
The consumer can be deployed and started independently. Users can start the booster
together with FastAPI, or start consumption separately.

Because funboost.faas is based on metadata registered by funboost into Redis, it can
dynamically discover boosters. As long as the consumer function is deployed and online,
the web service does not need to restart at all — you can call it immediately via the
HTTP interface. Compared to traditional web development where adding a feature requires
adding an endpoint and restarting the server, funboost faas is incredibly convenient.
"""

from funboost import BoosterDiscovery,BoostersManager

if __name__ == '__main__':
    # Demonstrate BoosterDiscovery, which automatically scans and registers @boost decorators.
    # The effect is equivalent to directly importing the add and sub modules under task_funs_dir.
    BoosterDiscovery(
        project_root_path=r'D:\codes\funboost',
        booster_dirs=['examples/example_faas/task_funs_dir'],
         ).auto_discovery()

    print(BoostersManager.get_all_queues())

    BoostersManager.consume_group('test_group1')
