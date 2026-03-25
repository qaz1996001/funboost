import time
from functools import wraps
from funboost import boost

def my_deco(f):
    wraps(f)
    def _inner(y):
        print('start executing',y)
        res = f(y)
        print('finish executing',y)
        return res
    return _inner


@boost('test2deco')
@my_deco
def fun(x):
    time.sleep(10)
    print(x)
    return x+10

if __name__ == '__main__':
    fun.push(5)
    fun.consume()



    # for i in range(10):
    #     fun.push(i)
    # fun.consume()
    # fun.multi_process_consume(2)