
import os
import sys
os.environ['path'] = os.path.dirname(sys.executable) + os.pathsep + os.environ['PATH']

"""
This demo demonstrates funboost's new support for pickle serialization.
When the consuming function's parameters are not basic types but custom types, funboost can automatically detect this
and serialize the relevant fields to strings using pickle.
When the consuming function runs, funboost automatically deserializes the pickle strings back to objects
and assigns them to the consuming function parameters.
"""

from pydantic import BaseModel
from funboost import (boost, BoosterParams, BrokerEnum, ctrl_c_recv, fct)


class MyClass:
    def __init__(self,x,y):
        self.x = x
        self.y = y

    def change(self,n):
        self.x +=n
        self.y +=n

    def __str__(self):
        return f'<MyClass(x={self.x},y={self.y})>'

    def __repr__(self):
        return f'<MyClass(x={self.x},y={self.y})>'

class MyPydanticModel(BaseModel):
    str1:str
    num1:int


@boost(BoosterParams(queue_name='queue_json_test',concurrent_num=10,is_using_rpc_mode=True,
                     broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def func0(m:str,n:int,q:dict,r:list): # Previously only supported this type of parameter; parameters had to be simple basic types.
    print(f'm:{m},n:{n}')
    print(f'q:{q},r:{r}')
   


@boost(BoosterParams(queue_name='queue_pickle_test',concurrent_num=10,is_using_rpc_mode=True,
                     broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def func1(a:MyClass,b:str,c:MyPydanticModel): # Now supports custom type objects as parameters.
    # print(fct.full_msg) # 可以查看原始消息
    print(f'a:{a}')
    print(f'b:{b}')
    print(f'c:{c}')
    print(f'a.x:{a.x},a.y:{a.y}')


if __name__ == '__main__':
    func0.consume()
    func1.consume()

    obj1 = MyClass(1,2)
    func1.push(obj1,'hello',MyPydanticModel(str1='hello',num1=1))  # Now supports publishing objects that cannot be JSON-serialized.

    obj1.change(10)
    func1.push(obj1,'hello',MyPydanticModel(str1='world',num1=100))

    func0.push('hello',100,{'a':1,'b':2},[1,2,3])  # Previously only allowed publishing messages with basic type parameters.
   
    ctrl_c_recv()






