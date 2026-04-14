import inspect
import nb_log
from funboost import BoosterParams
from funboost.utils.redis_manager import RedisMixin
from functools import wraps


def incr_deco(redis_key):
    def _inner(f):
        @wraps(f)
        def __inner(*args, **kwargs):
            result = f(*args, **kwargs)
            RedisMixin().redis_db_frame.incr(redis_key)
            # Create index

            # MongoMixin().mongo_client.get_database('basea').get_collection('cola').insert({'result':result,'args':str(args),'kwargs':str(kwargs)})
            return result

        return __inner

    return _inner


@BoosterParams(queue_name='test_queue_23b',
               should_check_publish_func_params=False,  # This line is important; should_check_publish_func_params must be set to False. When the decorator is applied directly to the function, funboost cannot obtain the function's parameter names and cannot auto-generate the JSON message, so the user must use publish to send the parameter dictionary.
               )
@incr_deco('test_queue_23b_run_count')
def fun(xxx, yyy):
    print(xxx + yyy)
    return xxx + yyy


if __name__ == '__main__':

    for i in range(20):
        # fun.push(i, 2 * i) # Cannot publish this way with fun.push
        fun.publish({'xxx': 1, 'yyy': 2})  # When the decorator is applied directly to the consumer function, the user must use publish to push and set should_check_publish_func_params=False in the boost decorator
    fun.consume()
