import sys
from pathlib import Path

current_dir = str(Path(__file__).parent)

sys.path.insert(4, current_dir) # This is to increase priority here. For example, if the user has installed the aioredis package, when running funboost, the aioredis package in this folder will be imported first. Better than sys.path.append.
# sys.path.append(current_dir)
