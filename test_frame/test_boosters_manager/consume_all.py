from pathlib import Path

import queue_names
from funboost import BoostersManager, BoosterDiscovery

# import mod1, mod2  # This must be imported; you can skip it but it's required so BoostersManager knows about @boost decorators in related modules. Or use BoosterDiscovery.auto_discovery() below to auto-import mod1 and mod2.



if __name__ == '__main__':
    """ Some people don't want to write code like this, calling .consume() on each function individually.
    They can use BoostersManager-related methods to start certain queues or all queues.
    mod1.fun1.consume()
    mod2.fun2a.consume()
    mod2.fun2b.consume()
    """
    BoosterDiscovery(project_root_path=Path(__file__).parent.parent.parent, booster_dirs=[Path(__file__).parent]).auto_discovery()  # Run this inside main to prevent infinite loop

    # Choose which queue names to consume
    # BoostersManager.consume(queue_names.q_test_queue_manager1,queue_names.q_test_queue_manager2a)

    # Choose which queue names to consume, with different numbers of consumer processes per queue
    # BoostersManager.mp_consume(**{queue_names.q_test_queue_manager1: 2, queue_names.q_test_queue_manager2a: 3})

    # Start consuming all queues in the same process
    BoostersManager.consume_all()

    # Start consuming all queues with n separate processes per queue
    # BoostersManager.mp_consume_all(2)
