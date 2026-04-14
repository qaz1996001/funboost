import sys

import copy
from funboost import BoosterParams, boost
from funboost.constant import FunctionKind
from funboost.utils.class_utils import ClsHelper

print('aaaaaaa')

class Myclass:
    m = 1

    def __init__(self, x):
        # This line is important: if an instance method is used as the consuming function, obj_init_params must be defined to save the __init__ parameters, used to reconstruct the object.
        self.obj_init_params: dict = ClsHelper.get_obj_init_params_for_funboost(copy.copy(locals()))
        # self.obj_init_params = {'x':x}  # The above line is equivalent to this one. If there are too many __init__ params, writing them to a dict one by one is tedious; use the above approach.
        self.x = x

    @boost(BoosterParams(queue_name='instance_method_queue', is_show_message_get_from_broker=True,qps=2 ))
    def instance_method(self, y):
        print(self.x + y)  # This sum uses both instance attributes and method parameters, demonstrating why self must be passed when publishing a message.

    #
    @classmethod
    @BoosterParams(queue_name='class_method_queue', is_show_message_get_from_broker=True,qps=2 )
    def class_method(cls, y):
        print(cls.m + y)

    @staticmethod
    @BoosterParams(queue_name='static_method_queue', is_show_message_get_from_broker=True,qps=2)
    def static_method(y):
        print(y)


@BoosterParams(queue_name='common_fun_queue', is_show_message_get_from_broker=True,qps=2)
def common_f(y):
    print(y)


if __name__ == '__main__':
    # print(sys.modules)

    for i in range(6, 100):
        Myclass.instance_method.push(Myclass(i), i * 2)  # Note the publish form: instance method publishing cannot be written as Myclass(i).push(i * 2); self must also be passed.
    Myclass.instance_method.consume()

    for i in range(6, 100):
        Myclass.class_method.push(Myclass,i * 2)  # Note the publish form: not Myclass.class_method.push(i * 2), but Myclass.class_method.push(Myclass, i * 2); cls must also be passed.
    Myclass.class_method.consume()

    for i in range(100):
        Myclass.static_method.push(i * 2)  # No special publish form needed; same as publishing a regular function.
    Myclass.static_method.consume()

    for i in range(100):
        common_f.push(i * 2)
    common_f.consume()
