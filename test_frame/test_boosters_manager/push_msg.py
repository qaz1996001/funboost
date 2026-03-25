from pathlib import Path

import queue_names
from funboost import BoostersManager, BoosterDiscovery

# import mod1, mod2  # This must be imported; you can skip it but it's required so BoostersManager knows about @boost decorators in related modules. Or use BoosterDiscovery.auto_discovery() below to auto-import m1 and m2 modules.


if __name__ == '__main__':
    BoosterDiscovery(project_root_path=Path(__file__).parent.parent.parent, booster_dirs=[Path(__file__).parent]).auto_discovery()  # Run this inside main to prevent infinite loop
    for x in range(10):
        BoostersManager.push(queue_names.Q_TEST_QUEUE_MANAGER1, x)
        BoostersManager.push(queue_names.Q_TEST_QUEUE_MANAGER2A, x * 20)
        BoostersManager.publish(queue_names.Q_TEST_QUEUE_MANAGER2B, {'x': x * 300})
